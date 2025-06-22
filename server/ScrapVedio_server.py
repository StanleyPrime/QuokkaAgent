import static_ffmpeg  # 或者 import imageio_ffmpeg as static_ffmpeg
static_ffmpeg.add_paths()   # 确保本进程 PATH 里有 ffmpeg/ffprobe

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from fastmcp import FastMCP
import os
import re

mcp = FastMCP("ScrapVideo_server")




@mcp.tool()
def download_videos(url: str,
                    output_dir: str = r"C:\Videos",
                    format_str: str = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]",
                    proxy: str = None,
                    use_cookies: bool = False,
                    browser: str = "chrome") -> str:
    """
    爬取指定网页的视频。有默认值的参数除非用户需求，否则无需指定。

    Params:
        url (str): 视频网页的 URL 地址。只要是视频url都可以尝试爬取。
        output_dir (str): 存放下载文件的目录，已有默认值
        format_str (str): yt-dlp 的 format 选项，已有默认值
        proxy (str): 可选，格式如 "socks5://127.0.0.1:1080"，已有默认值
        use_cookies (bool): 是否自动从浏览器读取 Cookies，已有默认值
        browser (str): 当 use_cookies=True 时，指定浏览器（"chrome", "firefox", "edge", "opera"），已有默认值

    Returns:
        str: 下载结果提示，成功时返回文件绝对路径，失败时返回错误原因。
    """
    # output_dir = to_container_path(output_dir)

    # 构建选项字典
    ydl_opts = {
        "format": format_str,
        "merge_output_format": "mp4",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "noplaylist": True,
    }
    if proxy:
        ydl_opts["proxy"] = proxy
    if use_cookies:
        # 从浏览器读取登录 Cookie
        ydl_opts["cookiesfrombrowser"] = browser

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # # 调用下载方法
            # ydl.download([url])
            # 提取并下载，extract_info 会返回视频信息字典
            info = ydl.extract_info(url, download=True)
            # 根据 info 生成最终文件名
            filename = ydl.prepare_filename(info)
        # 确保输出绝对路径
        basename = os.path.basename(filename)
        full_path = os.path.join(output_dir, basename)
        return f"视频成功下载到了{full_path}"
    except DownloadError as e:
        # yt-dlp 下载错误
        return f"视频爬取失败：下载错误，{str(e)}"
    except Exception as e:
        # 其它异常
        return f"视频爬取失败：{str(e)}"



if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8007)