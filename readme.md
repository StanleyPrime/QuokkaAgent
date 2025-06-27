# streamlit\_agent

> **将自主 AI 代理带到 Streamlit —— 构建你自己的 GUI-代理小助手。**

[![License](https://img.shields.io/github/license/StanleyPrime/streamlit_agent)]()
[![Docker Pulls](https://img.shields.io/docker/pulls/stanleyfeng/streamlit_agent)]()
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-red)]()

---

## ✨ 功能

* **基于聊天的界面** —— 由大型语言模型 (Gemini-2.5-Flash) 驱动
* **文件操作** —— 在容器内安全地读取、写入并浏览本地文件
* **YouTube 播放器** —— 内置搜索并在线播放视频，无需离开应用
* **图像生成** —— 根据文本提示创作图片并立刻下载
* **网页搜索** —— 使用 playwright 搜索互联网以获取信息
* **GoogleMap** —— 通过 Google Map API 查询并获取地图信息
* **数据分析** —— 代理可用 pandas 和 matplotlib 绘制图表、表格
* **视频抓取** —— 按需求从指定网站抓取视频
* **虚拟货币** —— 调用 CoinCapMarket API 获取虚拟货币数据
* **定时任务** —— 可以创建定时搜索分析任务或者定时提醒的任务
* **可扩展工具** —— 仅用一个 Python 装饰器即可添加自定义工具

---

## 🖥 演示

<div style="display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;">

  <div style="text-align: center;">
    <strong>演示 1</strong><br/>
    <img src="./gifs/demo1.gif" width="600px" alt="Demo1"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 2</strong><br/>
    <img src="./gifs/demo2.gif" width="600px" alt="Demo2"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 3</strong><br/>
    <img src="./gifs/demo3.gif" width="600px" alt="Demo3"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 4</strong><br/>
    <img src="./gifs/demo4.gif" width="600px" alt="Demo4"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 5</strong><br/>
    <img src="./gifs/demo5.gif" width="600px" alt="Demo5"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 6</strong><br/>
    <img src="./gifs/demo6.gif" width="600px" alt="Demo6"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 7</strong><br/>
    <img src="./gifs/demo7.gif" width="600px" alt="Demo7"/>
  </div>

  <div style="text-align: center;">
    <strong>演示 8</strong><br/>
    <img src="./gifs/demo8.gif" width="600px" alt="Demo8"/>
  </div>

</div>

> 📽 录屏展示了代理在七个场景中的表现，包括 Markdown 编辑、视频播放及图像生成等。

---

## 🚀 快速开始

### 🐳 使用 Docker 运行（推荐）

确保已安装并打开 Docker Desktop。

```bash
# 1）克隆仓库
git clone https://github.com/StanleyPrime/streamlit_agent.git

# 2）进入 **包含 `docker-compose.yml` 的文件夹**
cd streamlit_agent/docker

# 3）启动 🚀
docker compose up -d

# 然后在浏览器中打开 http://localhost:8501
```

### Docker 卷（可选）

若希望代理访问宿主机文件，可挂载驱动器（已配置好）：

```yaml
services:
  mcp:
    volumes:
      - "C:/:/mnt/c:cached"
      - "D:/:/mnt/d:cached"
```

### 💻 本地运行（开发模式）

```bash
# 1）克隆仓库
git clone https://github.com/<your-github-id>/streamlit_agent.git
cd streamlit_agent

# 2）可选但强烈推荐：创建并激活虚拟环境
python -m venv .venv
# ▶ Windows
.\.venv\Scripts\activate
# ▶ macOS / Linux
source .venv/bin/activate
# ▶ Anaconda
conda create -n streamlit_agent_test python=3.11
conda activate streamlit_agent_test

# 3）安装依赖
pip install -r requirements.txt

# 4）启动批处理脚本（将自动打开所有 servers.py 与 client.py）
agent.bat
```

---

## 🏗 项目结构

```
streamlit_agent/
├── .env
├── client.py               # Streamlit UI 客户端
├── pages/                  # documentaion.py
│   ├── servers_doc.py
│   ├── gemini_api_doc.py
├── server/                 # Fastmcp 服务器端
│   ├──.env
│   ├── file_system_server.py
│   ├── youtube_server.py
│   └── ...
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── requirements.txt
└── agent.bat
```

---

## 📌 路线图

* [ ] 🗣️ 语音聊天 / TTS
* [ ] 🤖 模型集成 —— 支持 OpenAI、Ollama 本地模型、DeepSeek、Qwen3 等
* [ ] 💾 持久化存储 —— 连接 MySQL 数据库以长期保存会话与聊天记录
* [ ] 🔧 扩展服务器能力 —— 代码调试工具、深度研究模块、省显存特性等
* [ ] 🌐 多语言支持 —— UI 与代理响应可使用更多语言
* [ ] 📊 分析面板 —— 跟踪使用指标、性能及代理效果
* [ ] 🎨 UI 自定义 —— 主题、布局选项及自定义组件支持
* [ ] 📱 移动友好 UI —— 响应式设计及 PWA 支持

完整功能提议请见 [open issues](https://github.com/<your-github-id>/streamlit_agent/issues)。

---

## 🤝 贡献

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feat/awesome`)
3. 提交变更 (`git commit -m 'Add some awesome'`)
4. 推送分支 (`git push origin feat/awesome`)
5. 打开 Pull Request

在提交 PR 前，请确保运行 **`pre-commit`**。

---

## 📄 许可证

基于 [MIT License](LICENSE) 分发。

---

## 🙏 致谢

* [Streamlit](https://streamlit.io)
* [OpenAI](https://openai.com)
* [LangChain](https://github.com/langchain-ai/langchain)
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* [Gemini](https://ai.google.dev/gemini-api/docs?hl=zh-cn)
* [bilibili-api](https://github.com/Nemo2011/bilibili-api)
* [fastmcp](https://github.com/jlowin/fastmcp)
* 以及所有贡献者 🤗
