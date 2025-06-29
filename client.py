import types
try:
    import torch

    # 伪造一个“类包路径对象”，满足监视器 list(module.__path__._path) 的要求
    class _FakePath(list):
        @property
        def _path(self):       # 必须带 _path
            return []          # 空列表即可

    torch.classes.__path__ = _FakePath()
except ImportError:
    pass
import asyncio, os, json
from dotenv import load_dotenv, set_key, dotenv_values
from pathlib import Path
from openai import OpenAI
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from copy import deepcopy
import streamlit as st
import time
import datetime
from pathlib import Path
import base64
import pandas as pd
import re
from unstructured.partition.pdf import partition_pdf
from typing import List

ENV_PATH = Path(__file__).with_name(".env")  # 100% 指向当前脚本所在目录
WINPATH_RE = re.compile(r'^([A-Za-z]):[\\/](.*)')


def to_container_path(path: str) -> str:
    """
    把  D:\folder\file.txt  →  /mnt/d/folder/file.txt
    非 Windows 路径则原样返回。
    """
    m = WINPATH_RE.match(path)
    if not m:
        return path  # 已经是 Linux 路径

    drive, rest = m.groups()
    # 先把所有反斜杠替换成斜杠
    rest = rest.replace("\\", "/")
    return f"/mnt/{drive.lower()}/{rest}"


def tools_to_gemini(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,  # ← 字段改名！
        },
    }


def tools_to_openrouter(tool):
    """
    将 MCP / 自定义工具描述转换为 OpenRouter (OpenAI-compatible) 的
    Chat-Function-Calling 工具格式。
    """
    # ---------- 1️⃣ 基础准备 ----------
    # • deepcopy 防止原始 schema 被我们就地修改
    # • schema 不一定含有 "type" / "properties" / "required" 键，需要兜底
    raw = deepcopy(tool.inputSchema) or {}

    schema = {
        "type": "object",
        # 如果原 schema 已经给出了 properties/required 就直接拿过来，否则给默认空字典/列表
        "properties": raw.get("properties", {}),
        "required": raw.get("required", []),
    }

    # ---------- 2️⃣ 为每个字段补全类型 ----------
    # 遵循 JSON-Schema Draft-07（OpenAI / OpenRouter 要求）
    for prop_name, prop_schema in schema["properties"].items():
        if "type" not in prop_schema:
            # 如果用户没写 type，默认按 string 处理
            prop_schema["type"] = "string"

        # 如果字段本身声明的是数组，但忘了 items，也要补上
        if prop_schema["type"] == "array" and "items" not in prop_schema:
            prop_schema["items"] = {"type": "string"}

    # ---------- 3️⃣ 组装最终工具描述 ----------
    return {
        "type": "function",
        "function": {
            "name": tool.name,  # 函数名
            "description": tool.description,  # 描述
            "parameters": schema,  # 完整 JSON-Schema
        },
    }


def stream_data(answer):
    for word in answer.split(" "):
        yield word + " "
        time.sleep(0.1)


def get_task():
    # 找到当前文件所在目录
    base_dir = Path(__file__).resolve().parent
    # 拼出 JSON 文件的完整路径
    json_path = base_dir / "Tasklist" / "Task.json"
    # 读取并解析
    with json_path.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not tasks:
        return "用户还未创建任何的定时任务"

    # 3. 拼接文本
    lines = []
    for idx, task in enumerate(tasks, start=1):
        name = task.get("TaskName", "")
        desc = task.get("Description", "")
        sched = task.get("Schedule", "")
        time = task.get("Time", "")
        date = task.get("Date", "")

        lines.append(f"任务{idx}：{name}")
        lines.append(f"任务描述: {desc}")

        # 根据 daily/once 分别处理
        if sched == "daily":
            lines.append(f"调度方式: 每日 {time} 执行一次")
        elif sched == "once":
            lines.append(f"调度方式: 在 {date} 的 {time} 执行一次")
        else:
            # 如果有其他类型，直接原样输出
            lines.append(f"调度方式: {sched} {date} {time}")

        # 分隔线
        if idx != len(tasks):
            lines.append("========================")

    # 4. 合并并输出
    result = "\n".join(lines)
    return result


TASK = get_task()


SYSTEM_MESSAGE = f"""
现在的时间是：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。
在此之前用户有可能创建了一系列的定时或每日自动执行的脚本任务，任务的内容如下：

{TASK}

你是一名严格遵守步骤的 AI 助手，当前可用工具有：

{{TOOLS}}

================== 任务说明 ==================
🔹 **第一步：判断用户意图是否明确**

1. **已明确**  
   - 如果用户输入已经包含清晰的目标、操作对象和期望结果  
     （如：“请帮我上网搜查比特币实时价格并把结果保存到 data/bitcoin.json”），  
     直接进入 *第二步·工作流*。

2. **不明确**  
   - 如果用户输入含糊或信息不足  
     （如仅输入“比特币”或“保存”），请先：  
     • 参考你能调用的工具，推测用户最可能的需求；  
     • 用一句简洁的中文向用户**先确认需求**，并顺带说明你能执行的选项，格式示例：  
       “请问您是想要 **___(推测的需求)___** 吗？如果是，我可以帮助你先**__(做的事情)__**,然后.....”  
     • 等待并读取用户的补充或确认；  
     • 只有在目标变得明确后，才进入 *第二步·工作流*。

🔹 **第二步：工作流**

1. 当任务需要工具时，先用中文说明【整体计划】；  
   例如：“好的，我将先查询温哥华的天气，然后把结果保存成 weather.json。”  
2. **同一条消息**里仅 **调用一个** tool（一次只能调用一个 tool）。  
3. 获得工具返回值后：  
   - 用中文总结当前进展，并决定下一步；  
   - 若还需其他工具，重复步骤 1–2；  
   - 若已完成所有步骤，则给出最终总结并结束。

⚠️ **禁止** 跳过步骤，也不要在一条消息里触发多个互相关联的工具。
"""


class MCPAgent:
    def __init__(self, endpoints: dict[str, str], api_key: str, base_url: str, model: str):
        self.endpoints = endpoints

        self.llm = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model

        self.tools = []
        self.tool_to_server = {}
        self.tool_desc = ""

        self.history = []

    async def connect(self):
        pulls = []
        for server, url in self.endpoints.items():
            async with Client(StreamableHttpTransport(url)) as cli:
                tools = await cli.list_tools()
                pulls.append((server, tools))

        for server, tools in pulls:
            for t in tools:
                if t.name in self.tool_to_server:
                    raise ValueError(f"存在重复的函数名{t.name}")
                self.tools.append(tools_to_gemini(t))  # 随时切换
                self.tool_to_server[t.name] = server

            joint = "\n".join(f"  - {t.name} —— {t.description}" for t in tools)
            self.tool_desc += f"\n 【{server}】\n {joint} \n"
            # print(self.tool_desc)

        self.history = [
            {"role": "system", "content": SYSTEM_MESSAGE.replace("{TOOLS}", self.tool_desc)}
        ]
        return self

    def ask(self, user_msg: str, image_list: List[dict]):
        if image_list:
            self.history.append(
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_msg}] + image_list
                }
            )
        else:
            self.history.append(
                {"role": "user", "content": user_msg}
            )

        while True:
            with st.spinner("🤔 正在思考中，请稍候…", show_time=True):
                choice = self.llm.chat.completions.create(
                    model=self.model,
                    reasoning_effort="high",
                    messages=self.history,
                    tools=self.tools,
                    tool_choice="auto"
                ).choices[0]

            if choice.finish_reason != "tool_calls":
                self.history.append(choice.message)
                return choice.message.content

            assistant_msg = choice.message
            safe_assistant = {
                "role": "assistant",
                "tool_calls": assistant_msg.tool_calls,
                # content 可能是 None / ""，一律替换成占位符
                "content": assistant_msg.content or " ",
            }
            self.history.append(safe_assistant)

            intro = (assistant_msg.content or "").strip()
            if intro:
                st.write(intro)
                st.session_state.messages.append({"role": "assistant", "content": intro})

            call = choice.message.tool_calls[0]
            name = call.function.name
            args = json.loads(call.function.arguments)

            if name == "show_image_frontend":
                image_path = args["image_path"].strip('"').strip("'")
                # image_path = to_container_path(image_path)
                st.image(image_path,width=300)
                self.history.append({
                    "role": "tool",
                    "tool_call_id": call.id,  # ← 一定要填 call.id
                    "name": name,  # ← 有些版本需要 name 字段
                    "content": "图片展示成功"
                })

                st.session_state.messages.append({"role": "assistant", "image": image_path})
            elif name == "show_video_frontend":
                video_path = args["video_path"].strip('"').strip("'")
                # video_path = to_container_path(video_path)
                st.video(video_path)
                self.history.append({
                    "role": "tool",
                    "tool_call_id": call.id,  # ← 一定要填 call.id
                    "name": name,  # ← 有些版本需要 name 字段
                    "content": "视频展示成功"
                })

                st.session_state.messages.append({"role": "assistant", "video": video_path})
            elif name == "show_dataframe_frontend":
                with st.container():
                    dataframe_path = args["dataframe_path"].strip('"').strip("'")
                    path = str(dataframe_path)
                    # path = to_container_path(path)
                    if path.lower().endswith(".csv"):
                        df = pd.read_csv(path)
                        st.dataframe(df)
                        st.session_state.messages.append({"role": "assistant", "dataframe": df})
                    elif path.lower().endswith((".xls", ".xlsx")):
                        df = pd.read_excel(path, sheet_name=0)
                        st.dataframe(df)
                        st.session_state.messages.append({"role": "assistant", "dataframe": df})
                    else:
                        raise ValueError("无法展示表格")
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": call.id,  # ← 一定要填 call.id
                        "name": name,  # ← 有些版本需要 name 字段
                        "content": "表格展示成功"
                    })
            elif name == "show_gif_frontend":
                gif_path = args["gif_path"].strip('"').strip("'")
                path = str(gif_path)
                with open(path, "rb") as f:
                    gif_bytes = f.read()
                b64 = base64.b64encode(gif_bytes).decode("utf-8")
                st.markdown(
                    f'<img src="data:image/gif;base64,{b64}" alt="动画">',
                    unsafe_allow_html=True
                )
                st.session_state.messages.append({"role": "assistant", "gif": gif_path})
                self.history.append({
                    "role": "tool",
                    "tool_call_id": call.id,  # ← 一定要填 call.id
                    "name": name,  # ← 有些版本需要 name 字段
                    "content": "gif图展示成功"
                })
            elif name =="read_image_file":
                image_path2 = args["path"].strip('"').strip("'")

                def encode_image_to_data_uri(image_path: str) -> str:
                    # 先猜一下文件的 MIME 类型
                    mime_type, _ = mimetypes.guess_type(image_path)
                    if mime_type is None:
                        # 如果猜不出来，就用扩展名简单拼一个
                        ext = os.path.splitext(image_path)[1].lstrip('.').lower()
                        mime_type = f"image/{ext}"

                    # 读文件并做 base64 编码
                    with open(image_path, "rb") as f:
                        data = f.read()
                    b64 = base64.b64encode(data).decode('utf-8')

                    # 拼成 Data URI
                    return f"data:{mime_type};base64,{b64}"
                data_uri = encode_image_to_data_uri(image_path2)

                self.history.append({
                    "role": "user",
                    "content": [{"type": "text", "text": "图片内容如上:"},
                                {"type": "image_url", "image_url": {"url": data_uri,"detail": "auto"}}]
                })
            else:
                with st.spinner(f"正在执行工具{name}", show_time=True):
                    server_name = self.tool_to_server[name]
                    url = self.endpoints[server_name]

                    async def _run_once():
                        async with Client(StreamableHttpTransport(url)) as cli:
                            return await cli.call_tool(name, args)

                    result = asyncio.run(_run_once())  # 保证 ask() 仍然是同步接口
                    # result 现在一定是 str / dict / bool … 可以被 JSON 序列化

                    self.history.append({
                        "role": "tool",
                        "tool_call_id": call.id,  # ← 一定要填 call.id
                        "name": name,  # ← 有些版本需要 name 字段
                        "content": json.dumps(result, ensure_ascii=False, default=str)
                    })
                st.success(f"工具{name}执行完毕")
                st.session_state.messages.append({"role": "assistant", "success": f"工具{name}执行完毕"})


# ① 先把 .env 读进来（如果文件不存在等会儿再创建）
load_dotenv(dotenv_path=ENV_PATH, override=False)
# ② 取出当前环境里的 KEY；没有就得到空字符串
gemini_key = os.getenv("GOOGLE_API_KEY", "")

# ───── 1. 可用服务总表（若已放在文件顶部可省略） ─────
AVAILABLE_SERVICES = {
    "文件系统服务": {
        "endpoint": "filesystem_server",
        "url": "http://127.0.0.1:8000/mcp",
        "needs_key": False,
        "env_var": None,  # 不需要则填 None
    },
    "谷歌地图": {
        "endpoint": "googlemap_server",
        "url": "http://127.0.0.1:8001/mcp",
        "needs_key": True,  # 需要额外 Key
        "env_var": "GOOGLE_MAPS_API_KEY",
    },
    "高德地图服务": {
        "endpoint": "amap_server",
        "url": "http://127.0.0.1:8002/mcp",
        "needs_key": True,  # 需要额外 Key
        "env_var": "AMAP_API_KEY",
    },
    "BiliBili服务": {
        "endpoint": "bilibili_server",
        "url": "http://127.0.0.1:8003/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "代码执行服务": {
        "endpoint": "code_executed_server",
        "url": "http://127.0.0.1:8004/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "虚拟货币数据服务": {
        "endpoint": "CoinMarketCap_server",
        "url": "http://127.0.0.1:8005/mcp",
        "needs_key": True,  # 需要额外 Key
        "env_var": "COINMARKETCAP_API_KEY",
    },
    "图片生成服务": {
        "endpoint": "Draw_server",
        "url": "http://127.0.0.1:8006/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "视频爬取服务": {
        "endpoint": "ScrapVideo_server",
        "url": "http://127.0.0.1:8007/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "Streamlit前端渲染服务": {
        "endpoint": "streamlit_server",
        "url": "http://127.0.0.1:8008/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "网页查询服务": {
        "endpoint": "WebSearch_server",
        "url": "http://127.0.0.1:8009/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    },
    "youtube视频服务": {
        "endpoint": "youtube_server",
        "url": "http://127.0.0.1:8010/mcp",
        "needs_key": True,  # 需要额外 Key
        "env_var": "YOUTUBE_API_KEY",
    },
    "定时任务服务":{
        "endpoint":"mornitor_server",
        "url":"http://127.0.0.1:8011/mcp",
        "needs_key": True,  # 需要额外 Key
        "env_var": "PUSHDEER_API_KEY",
    },
    "视频处理服务":{
        "endpoint":"mornitor_server",
        "url":"http://127.0.0.1:8012/mcp",
        "needs_key": False,  # 需要额外 Key
        "env_var": None,
    }

    # 下面想开哪个就放哪个，同理添加
    # "CoinMarketCap": {...}
}

st.markdown("### Streamlit_agent")

# 把pages下面的所有导航栏在sidebar中进行隐藏
st.markdown("""
<style>
/* 隐藏多页导航那块 */
div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ───── 2. Sidebar ─────
with st.sidebar:
    # ---------- A. 录入 / 更新 Gemini Key ----------
    st.header("🔑 Google Gemini API-Key")
    if st.button("Gemini api key获取方法"):
        # st.page_link("pages/gemini_api_doc.py", label="Gemini api key document", icon="1️⃣")
        st.switch_page("pages/gemini_api_doc.py")
    api_input = st.text_input(
        "GOOGLE_API_KEY",
        value=os.getenv("GOOGLE_API_KEY", ""),
        type="password",
        placeholder="AIzaSy......",
        key="gemini_key_input",
    )
    if st.button("保存 / 更新 Gemini Key", key="save_gemini_btn"):
        if api_input.strip():
            ENV_PATH.touch(exist_ok=True)
            set_key(ENV_PATH, "GOOGLE_API_KEY", api_input.strip(),quote_mode="never")
            load_dotenv(ENV_PATH, override=True)
            st.session_state.pop("agent", None)
            st.success("Gemini Key 已保存 ✅")
            st.rerun()
        else:
            st.error("Key 不能为空！")

    st.divider()

    # ---------- B. 选择并配置子服务 ----------
    st.subheader("🛠 mcp服务配置")
    if st.button("mcp服务说明文档"):
        st.switch_page("pages/servers_doc.py")
    with st.expander("点击展开 / 折叠服务列表", expanded=False):
        # ① 逐项渲染 checkbox +（可选）Key 输入框
        chosen = []
        key_inputs = {}
        for label, meta in AVAILABLE_SERVICES.items():
            enabled = st.checkbox(
                label,
                value=label in st.session_state.get("selected_services", []),
                key=f"chk_{label}",
            )
            if enabled:
                chosen.append(label)
                if meta["needs_key"]:
                    key_val = st.text_input(
                        f"{label} 的 {meta['env_var']}",
                        value=os.getenv(meta["env_var"]),
                        type="password",
                        key=f"key_{label}",
                        help="启用此服务前必须填写有效 API-Key,参考MCP服务文档",
                    )
                    key_inputs[label] = key_val

        # ② 提交按钮
        if st.button("提交配置", key="submit_svcs_btn"):
            errors = []
            # a. 验证必填 Key
            for lbl in chosen:
                meta = AVAILABLE_SERVICES[lbl]
                if meta["needs_key"]:
                    val = key_inputs.get(lbl, "").strip()
                    if not val:
                        errors.append(f"❌ {lbl} 缺少 API-Key")
                    else:
                        ENV_PATH.touch(exist_ok=True)
                        set_key(ENV_PATH, meta["env_var"], val)
                        os.environ[meta["env_var"]] = val  # 立即生效

            if errors:
                st.error(" \n".join(errors))
            else:
                st.session_state["selected_services"] = chosen
                load_dotenv(ENV_PATH, override=True)  # 重新加载全部 Key
                st.session_state.pop("agent", None)  # 使旧 Agent 失效
                st.success("服务配置已保存 ✅")
                st.rerun()

# ───── 3. 生成 endpoints 字典（放 Sidebar 之后、build_agent 之前） ─────
if "selected_services" not in st.session_state:
    st.session_state["selected_services"] = ["文件系统服务", "Streamlit前端渲染服务"]

endpoints = {
    AVAILABLE_SERVICES[lbl]["endpoint"]: AVAILABLE_SERVICES[lbl]["url"]
    for lbl in st.session_state["selected_services"]
}
if not endpoints:
    st.sidebar.warning("至少勾选一个服务才能启动聊天 🚦")
    st.stop()


def build_agent(api_key: str, endpoints: dict):
    model_name = "gemini-2.5-flash"
    endpoints = endpoints
    base_url = os.getenv("GOOGLE_BASE_URL")

    agent = asyncio.run(
        MCPAgent(
            endpoints=endpoints,
            model=model_name,
            api_key=api_key,
            base_url=base_url,
        ).connect()
    )
    return agent


# ───────────────── 主流程 ─────────────────
if "agent" not in st.session_state:
    key_in_env = os.getenv("GOOGLE_API_KEY", "")
    if key_in_env:  # ✅ 已有 KEY，安全初始化
        st.session_state.agent = build_agent(key_in_env, endpoints)
    else:  # ❌ 还没有 KEY，提示用户去填
        st.info("请在左侧填写 GOOGLE_API_KEY 后点击保存再开始聊天")
        st.stop()  # 终止本次执行，等待用户输入

agent = st.session_state.agent

# 初始化聊天历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []


def group_by_role(messages):
    """把相邻、角色相同的消息合成一个分组。"""
    groups = []
    for msg in messages:
        if groups and groups[-1]["role"] == msg["role"]:
            groups[-1]["messages"].append(msg)
        else:
            groups.append({"role": msg["role"], "messages": [msg]})
    return groups


# 先做分组
grouped_msgs = group_by_role(st.session_state.messages)

# 再逐组渲染
for group in grouped_msgs:
    role = group["role"]
    with st.chat_message(role):
        for msg in group["messages"]:
            if msg.get("image"):
                st.image(msg["image"],width=200)
            elif msg.get("video"):
                st.video(msg["video"])
            elif msg.get("text"):
                st.markdown(msg["text"])
            elif msg.get("content"):
                st.markdown(msg["content"])
            elif msg.get("success"):
                st.success(msg["success"])
            elif msg.get("download"):  # ← 新增
                meta = msg["download"]
                st.download_button(
                    label=meta["label"],
                    data=meta["data"],
                    file_name=meta["file_name"],
                    mime=meta["mime"],
                )
            elif msg.get("gif"):
                with open(msg["gif"], "rb") as f:
                    gif_bytes = f.read()
                b64 = base64.b64encode(gif_bytes).decode("utf-8")
                st.markdown(
                    f'<img src="data:image/gif;base64,{b64}" alt="动画">',
                    unsafe_allow_html=True
                )

if prompt := st.chat_input(
        "ask any question or upload image or file",
        accept_file=True,
        file_type=["jpg", "jpeg", "png", "pdf", "txt", "py", "md","mp4"],
):
    full_prompt = ""
    data_uri_list = []

    if prompt and prompt["files"]:
        for i, uploaded in enumerate(prompt["files"]):
            name = uploaded.name.lower()
            file_bytes = uploaded.read()
            uploaded.seek(0)

            if name.endswith(("jpg", "jpeg", "png")):
                base64_str = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{uploaded.type};base64,{base64_str}"
                data_uri_list.append({"type": "image_url", "image_url": {"url": data_uri,"detail": "auto"}})
                with st.chat_message("user"):
                    st.image(uploaded, width=200)
                st.session_state.messages.append({"role": "user", "image": uploaded})
            elif name.endswith("pdf"):
                elements = partition_pdf(file=uploaded)
                # 把所有段落拼成一个大字符串
                text = "\n\n".join(
                    e.text for e in elements
                    if hasattr(e, "text") and e.text.strip()
                )
                st.download_button(
                    label=f"📑 {uploaded.name}",
                    data=file_bytes,
                    file_name=uploaded.name,
                    mime="application/pdf",
                )
                # —— 把同样的元数据塞到聊天历史 ——
                st.session_state.messages.append({
                    "role": "user",
                    "download": {  # 这里的键名随便取，只要你自己识别得出来
                        "label": f"📑 {uploaded.name}",
                        "data": file_bytes,
                        "file_name": uploaded.name,
                        "mime": "application/pdf",
                    }
                })

                full_prompt += f"\n用户上传的第{i}个文档内容如下：\n\n{text}"
            elif name.endswith("py"):
                code = file_bytes.decode("utf-8")
                st.download_button(
                    label=f"🐍 {uploaded.name}",
                    data=file_bytes,
                    file_name=uploaded.name,
                    mime="text/x-python",
                )
                # —— 把同样的元数据塞到聊天历史 ——
                st.session_state.messages.append({
                    "role": "user",
                    "download": {  # 这里的键名随便取，只要你自己识别得出来
                        "label": f"📑 {uploaded.name}",
                        "data": file_bytes,
                        "file_name": uploaded.name,
                        "mime": "application/pdf",
                    }
                })
                full_prompt += f"\n用户上传的第{i}个文档内容如下：\n\n{code}"
            elif name.endswith("md"):
                md = file_bytes.decode("utf-8")
                full_prompt += f"\n用户上传的第{i}个文档内容如下：\n\n{md}"
                st.download_button(
                    label=f"📝 {uploaded.name}",
                    data=file_bytes,
                    file_name=uploaded.name,
                    mime="text/markdown",
                )
                # —— 把同样的元数据塞到聊天历史 ——
                st.session_state.messages.append({
                    "role": "user",
                    "download": {  # 这里的键名随便取，只要你自己识别得出来
                        "label": f"📑 {uploaded.name}",
                        "data": file_bytes,
                        "file_name": uploaded.name,
                        "mime": "application/pdf",
                    }
                })
            elif name.endswith("txt"):
                txt = file_bytes.decode("utf-8")
                full_prompt += f"\n用户上传的第{i}个文档内容如下：\n\n{txt}"
                st.download_button(
                    label=f"📄 {uploaded.name}",
                    data=file_bytes,
                    file_name=uploaded.name,
                    mime="text/plain",
                )
                # —— 把同样的元数据塞到聊天历史 ——
                st.session_state.messages.append({
                    "role": "user",
                    "download": {  # 这里的键名随便取，只要你自己识别得出来
                        "label": f"📑 {uploaded.name}",
                        "data": file_bytes,
                        "file_name": uploaded.name,
                        "mime": "application/pdf",
                    }
                })
            elif name.endswith("mp4"):
                # 2) 构造要保存的路径
                save_dir = Path(__file__).resolve().parent/"videos"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir,name)
                # 3) 写入文件
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                st.video(save_path)
                st.session_state.messages.append({"role":"user","video":save_path})
                full_prompt += f"\n用户上传了一个视频文件，视频文件的绝对路径是:{save_path}"
            else:
                st.info("不支持此文件格式")
    if prompt and prompt.text:
        with st.chat_message("user"):
            st.markdown(prompt.text)
            full_prompt += f"\n\n\n 用户的问题:\n {prompt.text}"
            st.session_state.messages.append({"role": "user", "text": prompt.text})

    with st.chat_message("assistant"):
        answer = agent.ask(full_prompt, data_uri_list)
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
