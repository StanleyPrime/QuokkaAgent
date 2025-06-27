# streamlit\_agent

> **Bring autonomous AI agents to Streamlit — build your own GUI‑first assistant.**

[![License](https://img.shields.io/github/license/StanleyPrime/streamlit_agent)]()
[![Docker Pulls](https://img.shields.io/docker/pulls/stanleyfeng/streamlit_agent)]()
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-red)]()

---

## ✨ Features

* **Chat‑based interface** powered by large language models (Gemini-2.5-Flash)
* **File operations** — read, write and browse local files securely inside the container
* **YouTube player** — search and play videos inline without leaving the app
* **Image generation** — create pictures from text prompts and download them instantly
* **Websearch** — using playwright to search the internet and gain information
* **GoogleMap** — search query from google-map api to gain information from the map.
* **data analyse** —agent can draw diagram,chart,table using pandas and matplotlib.
* **Video Scraping** —scraping videos from specific website if you ask agent.
* **Virtual Currency** —get virtual Currency data from CoinCapMarket API.
* **Extensible tools** — add your own agent tools with a single Python decorator

---
## 🖥 Demo

<div style="display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;">

  <div style="text-align: center;">
    <strong>Demo 1</strong><br/>
    <img src="./gifs/demo1.gif" width="600px" alt="Demo1"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 2</strong><br/>
    <img src="./gifs/demo2.gif" width="600px" alt="Demo2"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 3</strong><br/>
    <img src="./gifs/demo3.gif" width="600px" alt="Demo3"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 4</strong><br/>
    <img src="./gifs/demo4.gif" width="600px" alt="Demo4"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 5</strong><br/>
    <img src="./gifs/demo5.gif" width="600px" alt="Demo5"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 6</strong><br/>
    <img src="./gifs/demo6.gif" width="600px" alt="Demo6"/>
  </div>

  <div style="text-align: center;">
    <strong>Demo 7</strong><br/>
    <img src="./gifs/demo7.gif" width="600px" alt="Demo7"/>
  </div>

</div>

> 📽 Recordings show the agent across seven demos, including Markdown editing, video playback, and image generation.

---


## 🚀 Getting Started

### 🐳 Run with Docker (recommended)

make sure you have docker-desktop installed and open it.

```bash
# 1) Clone the repository
git clone https://github.com/StanleyPrime/streamlit_agent.git

# 2) Jump into the folder **that contains `docker-compose.yml`**
cd streamlit_agent/docker

# 3) Fire it up 🚀
docker compose up -d

# then open http://localhost:8501 in your browser
```


### Docker volumes (optional)

If you want the agent to access host files, mount your drives(already did):

```yaml
services:
  mcp:
    volumes:
      - "C:/:/mnt/c:cached"
      - "D:/:/mnt/d:cached"
```

### 💻 Run locally (dev mode)

```bash
# 1) Clone the repository
git clone https://github.com/<your-github-id>/streamlit_agent.git
cd streamlit_agent

# 2) (Optional but strongly recommended) create and activate a virtual environment
python -m venv .venv
# ▶ Windows
.\.venv\Scripts\activate
# ▶ macOS / Linux
source .venv/bin/activate
# ▶ Anaconda
conda create -n streamlit_agent_test python=3.11
conda activate streamlit_agent_test

# 3) Install dependencies
pip install -r requirements.txt

# 4) Launch the bat script(it will open all the servers.py and client.py)
agent.bat
```

---

## 🏗 Project Structure

```
streamlit_agent/
├── .env
├── client.py               # Streamlit UI client
├── pages/                  # documentaion.py
│   ├── servers_doc.py
│   ├── gemini_api_doc.py
├── server/                 # Fastmcp servers
│   ├──.env
│   ├── file_system_server.py
│   ├── youtube_server.py
│   └── ...
├── docker/
│   ├── Dockerfile
│   └── docker‑compose.yml
└── requirements.txt
└── agent.bat
```

---

## 📌 Roadmap

* [ ] 🗣️ Voice chat / TTS  
* [ ] 🤖 Model integrations — add support for OpenAI, Ollama local models, DeepSeek, Qwen3, etc.  
* [ ] 💾 Persistent storage — connect a MySQL database to retain sessions and chat history long-term  
* [ ] 🔧 Expanded server capabilities — code debugging tools, deep-research modules, memory-saving features, and more  
* [ ] 🌐 Multi-language support — UI and agent responses in additional languages  
* [ ] 📊 Analytics dashboard — track usage metrics, performance, and agent effectiveness  
* [ ] 🎨 UI customization — theming, layout options, and custom component support  
* [ ] 📱 Mobile-friendly UI — responsive design and PWA support  

See the [open issues](https://github.com/<your-github-id>/streamlit_agent/issues) for the full list of proposed features.

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feat/awesome`)
3. Commit your changes (`git commit -m 'Add some awesome'`)
4. Push to the branch (`git push origin feat/awesome`)
5. Open a pull request

Make sure you run **`pre‑commit`** before opening a PR.

---

## 📄 License

Distributed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

* [Streamlit](https://streamlit.io)
* [OpenAI](https://openai.com)
* [LangChain](https://github.com/langchain-ai/langchain)
* [yt‑dlp](https://github.com/yt-dlp/yt-dlp)
* [Gemini](https://ai.google.dev/gemini-api/docs?hl=zh-cn)
* [bilibili-api](https://github.com/Nemo2011/bilibili-api)
* [fastmcp](https://github.com/jlowin/fastmcp)
* And every contributor 🤗
