import asyncio
import os
import re
from typing import List
import datetime as dt
from bilibili_api import search, video, request_settings
from bilibili_api.search import SearchObjectType, OrderVideo
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
from fastmcp import FastMCP
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=True)


mcp = FastMCP("bilibili_server")


# ————————————————————————————————————————
# 如需代理，取消下注释
# request_settings.set_proxy("http://127.0.0.1:7890")
# ————————————————————————————————————————

# 合法 BV 号正则： BV 开头 + 10 位大小写字母/数字
BV_RE = re.compile(r"^BV[0-9A-Za-z]{10}$")


async def fetch_search(keyword: str, page: int = 1, page_size: int = 20) -> List[dict]:
    """按照关键字抓取搜索结果，并只保留包含合法 bvid 的条目。"""
    raw = await search.search_by_type(
        keyword=keyword,
        search_type=SearchObjectType.VIDEO,
        order_type=OrderVideo.TOTALRANK,
        page=page,
        page_size=page_size,
    )

    # ——————— 结构兼容 ———————
    if isinstance(raw, list):
        data = raw
    elif "result" in raw:
        data = raw["result"]
    elif "data" in raw and "result" in raw["data"]:
        data = raw["data"]["result"]
    else:
        data = []

    # 过滤掉没有或非法 bvid 的条目（广告 / 专栏 / 话题 等）
    return [item for item in data if isinstance(item, dict) and BV_RE.match(item.get("bvid", ""))]


async def enrich(bvid: str) -> dict:
    """根据 BV 号拉取详情并补齐统计/时间等字段。"""
    url = f"https://www.bilibili.com/video/{bvid}"
    v = video.Video(bvid=bvid)
    info = await v.get_info()
    stat = info.get("stat", {})

    # 发布时间：时间戳 → 可读格式
    ts = info.get("pubdate", 0)
    pubtime = dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "未知"

    return {
        "bvid": bvid,
        "url": url,
        "title": info.get("title", ""),
        "author": info.get("owner", {}).get("name", ""),
        "views": stat.get("view", 0),
        "likes": stat.get("like", 0),
        "comments": stat.get("reply", 0),
        "pubtime": pubtime,
        "desc": info.get("desc", ""),
    }


@mcp.tool()
async def search_and_enrich(query: str, keyword: str) -> str:
    """
通过输入关键词 keyword 从 bilibili视频网站中检索出多个视频的相关信息，然后内部会筛选出最符合要求的一条视频的标题和url
Params:
    query:string,用户自己的query，用来筛选视频的时候用的。
    keyword:String,搜索视频用的关键字，从用户的query中分析出这个keyword。
Return:
    返回的是一条视频的标题以及它的bilibili_url链接
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    page = 1
    page_size = 10

    base = await fetch_search(keyword, page, page_size)
    tasks = [enrich(item["bvid"]) for item in base]
    records = await asyncio.gather(*tasks)

    lines = [
        f"视频链接: {r['url']} | 标题: {r['title']} | 作者: {r['author']} | "
        f"发布时间: {r['pubtime']} | 观看量: {r['views']} | 点赞数: {r['likes']} | 评论数: {r['comments']}\n"
        for r in records
    ]
    video_markdown = "\n".join(lines)

    # ---- ② 组 prompt：系统提示 + 用户提问 + 视频候选 ----
    system_prompt = (
        "你是一位 B 站视频推荐助手。"
        "给定用户的问题和候选视频列表，你需要从发布时间,观看量和点赞量以及评论数进行分析,找出最符合用户需求的的一个视频"
        "补充说明:一般观看量或者点赞量越多的视频说明视频越受欢迎，所以筛选的时候可以以播放量和点赞数为优先选项。"
        "只回复 **一行**：`标题 | 链接`。如果没有合适的视频，回复 `暂无合适视频`。"
    )
    user_prompt = (
        f"**用户问题：** {query}\n\n"
        f"**候选视频列表：**\n{video_markdown}"
    )

    # ---- ③ 调用 OpenRouter（Qwen 3 235B a22b / free 版）----
    model = "gemini-2.0-flash"
    client = OpenAI(
        base_url=os.getenv("GOOGLE_BASE_URL"),
        api_key=os.getenv("GOOGLE_API_KEY"),
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    answer = resp.choices[0].message.content

    return answer


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003)