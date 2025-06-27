import streamlit as st

# 把pages下面的所有导航栏在sidebar中进行隐藏
st.markdown("""
<style>
/* 隐藏多页导航那块 */
div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    if st.button("返回主页面"):
        # st.page_link("pages/gemini_api_doc.py", label="Gemini api key document", icon="1️⃣")
        st.switch_page("client.py")


st.title("MCP各项服务说明")
st.markdown("---")

st.markdown("### 一.文件系统服务")
st.markdown('''##### 服务概述

该 MCP 文件系统服务提供了一套常用的文件和目录管理能力，旨在简化日常的文件操作流程。主要功能包括读取和写入文件、目录创建与列举、编辑文件、文件移动、内容搜索、元数据获取，以及文件或目录的删除等。

##### 功能一览

* **read\_file**：以 UTF-8 编码读取单个文件的全部内容。

* **read\_multiple\_files**：同时读取多份文件，批量获取它们的内容并返回结果。

* **write\_file**：创建新文件或覆盖已有文件，确保父目录存在后写入内容。

* **edit\_file**：对文件内容进行模式匹配式替换，支持演练模式查看差异或直接应用修改。

* **create\_directory**：创建指定目录（包含父目录），若目录已存在则静默通过。

* **list\_directory**：列出指定目录下的所有条目，并在名称前标注文件或目录。

* **move\_file**：将文件或目录移动或重命名，若目标已存在则阻止操作以免覆盖。

* **search\_files**：递归搜索文件或目录名，支持不区分大小写的匹配和自定义排除模式。

* **get\_file\_info**：获取文件或目录的详细元数据，如大小、类型、权限和时间戳等。

* **list\_allowed\_directories**：列出环境中允许访问的目录列表，可接收预定义列表或自动返回常见路径。

* **delete\_path**：删除指定文件或目录，支持空目录和递归删除，提供详细的错误提示。
''')
st.markdown("---")



st.write("")
st.write("")
st.markdown("### 二.高德地图服务")
st.markdown('''##### 服务概述

`高德地图` 服务基于 FastMCP 封装了高德地图的核心功能，提供统一的接口，可用于地点搜索、驾车路线和公交/地铁换乘规划，方便在 Web 或脚本中快速集成地图服务。

##### 功能一览

* **keyword\_search**: 根据关键词和城市搜索 POI（兴趣点），返回名称、地址、开放时间及评分等信息。
* **get\_amap\_driving\_route**: 驾车路线规划，提供总距离、预计时长、过路费、出租车预估费用以及详细导航步骤。
* **get\_amap\_transit\_route**: 公交/地铁换乘规划，列出多种换乘方案，包含预计耗时、步行距离、票价和详细换乘流程。
''')
st.markdown('''##### 配置apikey

高德地图的服务需要先去高德地图开放平台网站上获取apikey才能使用(申请后有每个月免费使用的次数)，官网请跳转:
''')
st.link_button("高德地图开放平台官网", "https://lbs.amap.com/?ref=https://console.amap.com/dev/index")
st.markdown("---")



st.write("")
st.write("")
st.markdown("### 三.BiliBili服务")
st.markdown('''##### 服务概述

**bilibili\_server** 是一个基于 FastMCP 框架搭建的 B 站视频推荐服务。它会根据用户的自然语言提问，自动在 B 站上检索相关视频，补充播放量、点赞数、评论数、发布时间等信息，再结合大语言模型（如 Gemini）对候选视频进行评估，最终挑选出最符合用户需求的一条视频并返回其标题和链接。

##### 功能概述

* **search\_and\_enrich**
  对用户问题进行理解，提取搜索关键词后调用 B 站搜索接口，筛选出合法的 BV 号视频；再批量拉取每条视频的播放量、点赞、评论、发布时间等元数据；最后将这些候选视频列表通过大语言模型分析——以播放量和点赞数优先，结合发布时间和评论数，从中挑出最符合用户需求的一条，并返回“标题 | 链接”的简洁推荐结果。

''')
st.markdown('''##### 配置apikey

这项服务默认调用了gemini语言模型的服务，apikey与你配置gemini的apikey相同。
''')
st.markdown("---")


st.write("")
st.write("")
st.markdown("### 四.代码执行服务")
st.markdown('''##### 服务概述

启动时会在项目目录下一次性创建并准备好一个 Python 虚拟环境，除了内置的模块以外，其中已预安装了 matplotlib、pandas、numpy。然后会通过这个环境来运行AI写出来的代码。

##### 功能一览

* **python\_code\_execution**
  在独立的虚拟环境中异步执行用户提供的 Python 代码块，环境中已包含常用数据分析和可视化库，无需额外安装。执行完成后返回标准输出或错误提示。
''')
st.markdown("---")


st.write("")
st.write("")
st.markdown("### 五.虚拟货币数据服务")
st.markdown('''##### 服务概述

调用 CoinMarketCap 官方 API，为用户提供加密货币市场行情数据。启动后监听在 8002 端口，支持批量获取前 N 名加密货币的整体行情概览，以及查询单个币种的实时详细数据。

##### 功能一览

* **get\_cryptos\_data**
  获取排名前 limit 的多种加密货币市场概览，包括名称、符号、CMC 排名、最大、流通、总供应量、交易对数量，以及多时段的价格、成交量、涨跌幅和市值等关键信息。

* **get\_specify\_crypto**
  查询指定符号（如 BTC、ETH 等）的一种加密货币的最新行情，返回其名称、CMC 排名、交易对数量、供应量，以及当前价格、各时段价格变化和市值等详细数据。
''')
st.markdown('''##### 配置apikey

这项服务需要CoinMarketCap 官方 APIkey才能使用，请前往官网注册apikey(申请后有每个月免费使用的次数)，官网请跳转:
''')
st.link_button("CoinMarketCap API 注册网址", "https://pro.coinmarketcap.com/account")
st.markdown("---")


st.write("")
st.write("")
st.markdown("### 六.图片生成服务")
st.markdown('''##### 概述

DrawServer 是一个基于 FastMCP 框架的图像生成微服务，集成了 Google GenAI（Gemini-2.0）模型。它根据用户提供的文本提示（prompt）智能生成图片，并将结果保存到服务器的指定路径，便于前端展示或后续处理。

##### 主要功能

* **draw\_image**
  该工具函数接收文本描述和图片名称，调用 Gemini-2.0-flash-preview-image-generation 模型生成图像，并将生成的图片以指定名称保存在C\\images文件夹中。

''')
st.markdown('''##### 配置apikey

这项服务默认调用了gemini语言模型的服务，apikey与你配置gemini的apikey相同。
''')
st.markdown("---")



st.write("")
st.write("")
st.markdown("### 七.视频爬取服务")
st.markdown('''

##### 服务概述

通过集成 **yt-dlp** 库，可以从指定的一些网页爬取视频并保存到本地自己指定的目录中，默认保存到C:/videos文件夹中。
可以爬取视频的网站有：Youtube,Bilibili,CNN等，其他可以参考：
''')
st.link_button("yt-dlp支持的视频网站", "https://ytdl-org.github.io/youtube-dl/supportedsites.html")
st.markdown('''##### 功能一览

* **download\_videos**
  使用 yt-dlp 从给定 URL 下载单个视频，并合并音视频流为 MP4 文件。
''')
st.markdown("---")

st.write("")
st.write("")
st.markdown("### 八.Streamlit前端渲染服务")
st.markdown('''##### 服务概述(请默认开启)

通过 Streamlit 前端快速展示多媒体内容。它将常见的图像和视频展示功能封装为可远程调用的工具，使得在 Web 应用或内部平台中集成媒体展示变得简单高效。

##### 功能一览
* **图片展示**：支持将服务器本地的 PNG、JPG 等格式图片渲染到前端界面，方便用户直观查看。
* **视频展示**：支持通过 Streamlit 播放本地 MP4 视频文件，也可以嵌入 YouTube 链接进行在线播放。
''')
st.markdown("---")



st.write("")
st.write("")
st.markdown("### 九.网页查询服务")
st.markdown('''##### 服务简介

通过duckduckgo搜索引擎上网页中获取相关的信息，加上他就可以理解成可以理解为SearchGPT的功能

##### 功能一览

* **search_and_analyse**：对输入的查询词并发获取 DuckDuckGo 搜索结果，加载页面并提取正文返回相关结果

''')
st.markdown("---")



st.write("")
st.write("")
st.markdown("### 十.youtube视频服务")
st.markdown('''##### 服务概述

本服务基于 YouTube Data API（v3）构建，主要用于对 YouTube 平台上的视频进行关键词搜索，并获取相关视频的统计信息。。

##### 功能一览

* **search\_videos\_with\_stats**：
  根据指定的关键词，在 YouTube 上检索相关视频，并批量获取视频的详细信息和统计数据，包括视频标题、上传者、观看次数、点赞数、评论数、发布时间及观看地址。

''')
st.markdown('''##### 配置apikey

这项服务同样需要去google官网配置apikey功能并开启服务，此项服务不与gemini服务共用，需要另外开启(申请后有每个月免费使用的次数)，官网请跳转:
''')
st.link_button("YouTube Data API（v3）申请", "https://console.cloud.google.com/apis/library/youtube.googleapis.com?inv=1&invt=Ab0dNw&project=chatapp-5e029")
st.markdown('''##### api配置教程：''')
if st.button("API配置教程"):
    st.switch_page("pages/youtube_api_doc.py")
st.markdown("---")


st.write("")
st.write("")
st.markdown("### 十一.定时任务服务")
st.markdown('''##### 服务概述

本服务可以创建定时提醒或者定时搜查内容的服务，服务开启以后只要电脑开机就可以在固定的时间执行搜查分析或者提醒服务，也同时可以定时往手机上发消息。
你可以用这项服务来构建提醒事项，也可以用来定时搜查和关注某些数据或者新闻。

##### 功能一览

* **create_search_task**：
    创建一个定时搜查并且分析的任务，比如想关注“比特币的最新价格和新闻”并做出分析，可以规定执行任务的时间，比如每天的早上8点钟执行这个任务。可以决定是否将得到的数据发送到手机上面。
* **sent_phone_task**：
    创建一个提醒事项，可以让ai提醒你在什么时候做什么事情，会在规定的时间发送消息到手机上面提醒你。
''')
st.markdown('''##### 配置apikey

这项服务只需要在手机上下载"PushDeer"的app(ios和安卓都有)，打开app后下方的第三个选项的key点开直接就有APIKEY(完全免费)。
''')
st.write("")
st.write("")

st.markdown("##### 更多服务敬请期待.....")







