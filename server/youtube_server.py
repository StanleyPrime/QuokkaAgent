from googleapiclient.discovery import build
from fastmcp import FastMCP
import os
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=False)

mcp = FastMCP("youtube_server")

@mcp.tool()
def search_videos_with_stats(query: str):
    """获取youtube官网上与query相关的视频的信息，获取到的信息里会包括视频的url，视频的标题和作者等信息
    Params:
        query:Sting,输入需要搜索的关键字，比如：“NBA总决赛highlights"
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    API_KEY = os.getenv("YOUTUBE_API_KEY")

    youtube = build("youtube", "v3", developerKey=API_KEY)

    # 第一步：搜索，拿到 videoId 列表
    search_resp = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=1
    ).execute()
    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]

    if not video_ids:
        return []

    # 第二步：批量获取详情（snippet + statistics）
    detail_resp = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    ).execute()

    final_result = ""

    videos = []
    for item in detail_resp.get("items", []):
        snip = item["snippet"]
        stats = item["statistics"]
        vid = item["id"]

        videos.append({
            "videoId": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "title": snip.get("title"),
            "description": snip.get("description"),
            "publishedAt": snip.get("publishedAt"),
            "uploader": snip.get("channelTitle"),
            "viewCount": stats.get("viewCount"),
            "likeCount": stats.get("likeCount"),
            "commentCount": stats.get("commentCount"),
        })

    for v in videos:
        final_result += (
                f"标题：     {v['title']}\n"
                f"上传者：   {v['uploader']}\n"
                f"观看次数： {v['viewCount']}\n"
                f"点赞数：   {v['likeCount']}\n"
                f"评论数：   {v['commentCount']}\n"
                f"发布时间： {v['publishedAt']}\n"
                f"视频地址： {v['url']}\n"
                + "-" * 60
                + "\n"
        )
    return final_result


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8010)
