import os

from fastmcp import FastMCP
from duckduckgo_search import DDGS
import asyncio
from playwright.async_api import async_playwright
import trafilatura
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=True)

mcp = FastMCP("Websearch_server")


def extract_text(html):
    """同步调用 trafilatura.extract 来提取文本"""
    return trafilatura.extract(html)


async def fetch_and_extract(url):
    """异步爬取网页并提取正文，遇到导航或加载错误时返回空字符串"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            java_script_enabled=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        # 屏蔽图片、CSS、字体等资源，加快速度
        await page.route("**/*", lambda route: route.abort()
                         if route.request.resource_type in ["image", "stylesheet", "font"]
                         else route.continue_())
        try:
            # 加上 wait_until='load'（默认）就足够，networkidle 有时反而卡住
            await page.goto(url, timeout=60000, wait_until="load")
        except Exception as e:
            print(f"[Warning] 无法导航到 {url}：{e}")
            await browser.close()
            return ""  # 跳过该页面

        full_html = await page.content()
        await browser.close()

        # trafilatura.extract 可能返回 None
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, extract_text, full_html)
        return text or ""


def get_urls(query,max_result):
    """获取 DuckDuckGo 搜索结果（此处获取2个结果作为示例）"""
    ddgs = DDGS()
    results = ddgs.text(
        keywords=query,  # 查询词
        region="wt-wt",  # 区域，wt-wt=不限区域
        safesearch="off",  # 过滤级别：on / moderate / off
        timelimit="d",  # 时限：d（天）/ w（周）/ m（月）/ y（年）或 None
        backend="auto",  # 请求后端：auto / html / lite
        max_results=max_result  # 最多结果数
    )
    return [res['href'] for res in results]


async def search(query,max_result):
    """并发地爬取多个网页，并返回拼接后的所有正文内容"""
    urls = get_urls(query,max_result)

    # 并发执行多个爬取、提取任务，得到各个URL的正文列表
    extracted_texts = await asyncio.gather(*(fetch_and_extract(url) for url in urls))

    # 将每个正文用 “\n========== 搜索结果 i ==========” 进行分割，一次性拼成一个字符串
    # 这里用列表推导式做拼接，也可以用 for loop，二者效果相同。
    combined_results = "\n\n".join(
        f"======================== 搜索结果 {i} ==========================\n{txt}"
        for i, txt in enumerate(extracted_texts, start=1)
        if txt
    )
    return combined_results


@mcp.tool()
async def search_and_analyse(query: str) -> str:
    """
    根据用户的 query 并发爬取网页、提取文本内容。
    """
    # 直接在当前事件循环中 await 而不是 asyncio.run
    results = await search(query, max_result=3)

    return results


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8009)