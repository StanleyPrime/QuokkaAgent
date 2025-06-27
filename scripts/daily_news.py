# daily_news.py
import datetime, argparse
import os
from pathlib import Path
from playwright.async_api import async_playwright
import trafilatura
import asyncio
from duckduckgo_search import DDGS
import json
from openai import OpenAI
import requests
from datetime import date
from typing import List, Dict,Optional
import subprocess
from dotenv import load_dotenv



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


async def search_and_analyse(query: str) -> str:
    """
    根据用户的 query 并发爬取网页、提取文本内容。
    """
    env_path = Path(__file__).resolve().parent.parent / '.env'

    # 2. 加载 .env
    load_dotenv(dotenv_path=env_path)

    # 直接在当前事件循环中 await 而不是 asyncio.run
    results = await search(query, max_result=3)

    # print("\n\n搜索到的结果:",results)

    SYSTEM_MESSAGE = f'''
你是一个专业的信息情报分析师。你的核心任务是接收用户提供的、由多个搜索结果组成的文本，并从中提取关键信息，然后以清晰、严格的时间线格式进行聚合与呈现。

请严格遵守以下指令：

1.  **核心目标**：创建一个按日期顺序排列的事件时间线。
2.  **信息来源**：只能使用用户提供的文本内容。严禁添加任何外部知识、猜测或评论。
3.  **聚合信息**：如果多个来源都提到了同一个事件，请将它们的细节（如参与人物、具体行动、各方表态）整合到该事件的描述中，避免信息重复。
4.  **输出格式**：
    * 直接开始输出内容，不要有任何的引言和开头。
    * 以日期作为一级标题，格式为“**YYYY年M月D日**”。
    * 在每个日期下，使用无序列表（bullet points, `-`）来列出当天发生的关键事件。
    * 每个事件的描述应简洁、客观、清晰。
5.  **处理原则**：如果信息中提到了某个事件发生的具体日期（如6月21日的空袭），就将其归入对应日期。如果信息是在某个日期发布的（如6月22日的表态），也将其归入该日期。
---
[用户信息]
搜索关键字: {query}

[待处理内容]
{results}
---

现在，请基于以上[待处理内容]，并严格按照指令生成时间线。
'''

    client = OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    completion = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {
                "role": "user",
                "content": SYSTEM_MESSAGE
            }
        ]
    )
    final_result = completion.choices[0].message.content
    # print("\n\n搜索总结出来的消息: ",final_result)
    return final_result


PROJECT_ROOT = Path(__file__).parents[1]          # 即 …/mornitor
OUT_DIR = PROJECT_ROOT / "news_logs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


TASK_FILE  = PROJECT_ROOT / "Tasklist" / "Task.json"
TASK_FILE.parent.mkdir(exist_ok=True)          # 确保 Tasklist 目录存在

# ------------------ 工具：读 / 写 JSON ------------------ #
def _load_tasks() -> List[Dict]:
    if TASK_FILE.exists():
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    return []

def _save_tasks(tasks: List[Dict]) -> None:
    TASK_FILE.write_text(
        json.dumps(tasks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def delete_task(task_name: str, *, force: bool = True) -> None:
    cmd = ["schtasks", "/delete", "/tn", task_name]
    if force:
        cmd.append("/f")
    subprocess.run(cmd, check=True, text=True)

    # 同步删除 JSON 记录
    tasks = _load_tasks()
    new_tasks = [t for t in tasks if t["TaskName"] != task_name]
    if len(new_tasks) != len(tasks):
        _save_tasks(new_tasks)
        print(f"[OK] Task.json 中已移除 {task_name}")
    print(f"[OK] 计划任务 {task_name} 已删除")


async def main(taskname: str, query: str, save_dir:str=None,sent_to_phone:bool=False) -> None:
    """爬取 query，结果追加到 news_logs/<taskname>.json"""
    env_path = Path(__file__).resolve().parent.parent / '.env'

    # 2. 加载 .env
    load_dotenv(dotenv_path=env_path)
    try:
        if save_dir:
            save_path = Path(save_dir).expanduser()
            # 若用户给的是相对路径，就挂到项目根目录下
            if not save_path.is_absolute():
                save_path = PROJECT_ROOT / save_path
        else:
            save_path = OUT_DIR  # <项目>/news_logs，已在顶端 mkdir 过

        save_path.mkdir(parents=True, exist_ok=True)
        outfile = save_path / f"{taskname}.json"

    except PermissionError as e:
        print(f"[ERROR] 没权限写入 {save_path}: {e}")
        # 回退到项目自带的 OUT_DIR，保证脚本不至于崩
        fallback = OUT_DIR
        fallback.mkdir(parents=True, exist_ok=True)
        outfile = fallback / f"{taskname}.json"
        print(f"[INFO] 回退到 {outfile}")


    # 1. 真正抓取
    result = await search_and_analyse(query)

    # 2. 载入旧数据
    if outfile.exists():
        news: list = json.loads(outfile.read_text(encoding="utf-8"))
    else:
        news = []

    # 1. 取出历史内容并序列化成纯文本
    old_news_json = json.dumps(news, ensure_ascii=False, indent=2)

    # 2. latest_timeline 就是前面 search_and_analyse 返回的 result
    latest_timeline = result

    SYSTEM_PROMPT = f"""
你是一名资深信息情报分析师，专门负责**连续事件跟踪**。
今天的日期是:{date.today()}

================== 任务说明 ==================
1. 你将看到两段时间线：
    [历史数据] —— 过去所有已记录事件，已按日期列出。
    [今日抓取] —— 刚刚从网络抓取并整理的事件时间线。
2. 如果 [今日抓取] 中的事件在 [历史数据] 中已经出现
    今日日期以前的信息如果已经在历史数据中有写到则视为“已记录”，**不要重复输出**。
    比如今日是6月24日，如果6月23日或之前的信息已经有了，则只需要获取到6月24日当天有的信息就好了。
    如果历史数据中没有6月24日以前的信息的话，就需要按时间线进行输出。
3. 如发现 [今日抓取] 中某事件：
    · 在历史中完全没有出现，或  
    · 虽然事件本身出现过，但**今天新增了重要细节**  
    —— 这两种情况都视为“新增信息”，必须输出。
4. 输出要求：
    * 直接开始输出内容，不要有任何的引言和开头
    * 仍按日期升序组织，一级标题格式 **YYYY年M月D日**。
    * 每个日期下用 bullet-point（-）列出“新增事件”或“新增细节”。
    * 每条 bullet 先给一句 ≤25 字的事件概括，再用 1-2 句补充重要细节（如责任方、伤亡数字等）。
5. 若确认 [今日抓取] 没有任何新增内容，输出固定一句：
    **今日无新增事件**。

================== 输入区 ==================
[历史数据]
{old_news_json}

[今日抓取]
{latest_timeline}
==========================================

现在开始比对并生成仅含“新增信息”的时间线。
"""

    client = OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    completion = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "user", "content": SYSTEM_PROMPT}
        ]
    )

    new_info = completion.choices[0].message.content

    SYSTEM_PROMPT2 = f'''
你是一名资深信息情报分析师，专门负责分析获取到的信息。
今天的日期是:{date.today()}

================== 任务说明 ==================
1. 你将看到根据query获取到的两段时间线：
    [query] —— 搜索时用到的关键字
    [历史数据] —— 过去所有已记录事件，已按日期列出。
    [今日抓取] —— 今日从网上获取到的最新数据。
2.你需要根据query和历史数据对今日抓取到的最新数据进行详细的分析，然后书写一份分析报告：
    比如：你可以先告诉用户今天发生了什么，然后分析发生了这个情况的原因等，然后你可以预测一下未来可能会发生哪些情况，我们需要做些什么准备等等的分析。
    又比如: 你可以告诉用户今天的爬取内容获取到了什么新的知识，这些知识能用来做什么，原理是什么？分析一下这个知识未来的展望等等分析。
    又比如: 你可以告诉用户今天的爬取内容得知了什么技术上的新进展，这项进展具体体现在什么地方，对我们有什么帮助，以及我们可以多加关注的点等等分析。
3. 输出要求：
    * 直接开始输出内容，不要有任何的引言和开头
    * 分析报告的开头写一个一级标签的标题

================== 输入区 ==================
[query]
{query}

[历史数据]
{old_news_json}

[今日抓取]
{latest_timeline}
==========================================

请开始写你的分析报告吧！
'''
    completion2 = client.chat.completions.create(
        model="gemini-2.5-flash",
        reasoning_effort="high",
        messages=[
            {"role": "user", "content": SYSTEM_PROMPT2}
        ]
    )
    final_report = completion2.choices[0].message.content

    # 3. 追加新纪录
    news.append({
        "search_time": datetime.datetime.now().isoformat(timespec="seconds"),
        "query":query,
        "delta_events": new_info  # 只保存新增事件
    })

    # 4. 保存
    try:
        # 尝试写入
        outfile.write_text(
            json.dumps(news, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[OK] 已写入 {outfile}")

    except Exception as e:
        # 捕获所有异常并输出
        print(f"[ERROR] 无法写入 {outfile}：{e!r}")

        await asyncio.sleep(30)
        # traceback.print_exc()  # 打印完整调用栈，定位到出错行
        # 如果希望错误继续向上抛，让计划任务失败并在日志可见，可再加：
        # raise


    pushkey = os.getenv("PUSHDEER_API_KEY")

    if sent_to_phone:
        url = "https://api2.pushdeer.com/message/push"
        data = {
            "pushkey": pushkey,
            "text": query,
            "desp": new_info + "\n" + final_report,
            "type": "markdown"  # 也可以 text / image
        }

        requests.post(url, data=data, timeout=10).raise_for_status()

        print("内容已经发送到手机端")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskname", required=True, help="计划任务名 / JSON 文件名前缀")
    parser.add_argument("--query", required=True, help="检索关键词")
    parser.add_argument("--save_dir", help="json文件保存的路径")
    parser.add_argument(
        "--sent_to_phone",
        action="store_true",  # 出现即 True，不出现即 False
        help="抓取完是否把结果发到手机"
    )
    parser.add_argument(
        "--self_destruct",
        action="store_true",
        help="脚本跑完后自动删除该一次性任务"
    )
    args = parser.parse_args()
    asyncio.run(main(args.taskname, args.query,args.save_dir,args.sent_to_phone))

    # 如果带了 --self_destruct，就调用 mornitor_news.delete_task
    if args.self_destruct:
        delete_task(args.taskname, force=True)
