import subprocess
from pathlib import Path
from typing import Union
from fastmcp import FastMCP
import os

mcp = FastMCP()


# 默认把 GIF 放在脚本同级的 “gifs/” 目录
DEFAULT_GIF_DIR = Path(__file__).resolve().parent.parent / "videos_to_gifs"


@mcp.tool()
def mp4_to_gif_ffmpeg(
    input_path: Union[str, Path],
    output_dir: Union[str, Path] = DEFAULT_GIF_DIR,
    fps: int = 20,
    max_colors: int = 256,
):
    """
    用纯 FFmpeg 把单个 MP4 或文件夹内所有 MP4 转成高质量 GIF，不做缩放。

    Params:
      input_path: 单个 .mp4 文件路径，或包含 .mp4 的文件夹路径
      output_dir: GIF 保存目录（如果是单文件，也可以是完整的 .gif 路径），有默认值，没有要求的话可以不填。
      fps: 输出 GIF 帧率，有默认值是20
      max_colors: palettegen 的最大颜色数，有默认值是256
    Return:
      视频转换成功的提示并且包含转换后保存的绝对路径。
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    # ---------- 目录模式：批量把文件夹里的 *.mp4 全部转 GIF ----------
    if input_path.is_dir():
        output_dir.mkdir(parents=True, exist_ok=True)
        for vid in input_path.glob("*.mp4"):
            mp4_to_gif_ffmpeg(
                vid,
                output_dir,  # 仍然传“目录”，递归时自动生成文件名
                fps=fps,
                max_colors=max_colors,
            )
        return f"已批量转换 {input_path} 下所有 MP4 到 {output_dir}"

    # ---------- 单文件模式：input_path 必须是 .mp4 ----------
    if not (input_path.is_file() and input_path.suffix.lower() == ".mp4"):
        raise ValueError(f"无效输入：{input_path} 既不是 mp4 文件也不是目录")

    # --- 1) 计算真正的输出 GIF 路径 ---
    if output_dir.suffix.lower() == ".gif":
        # 调用者给的是完整文件名
        output_gif = output_dir
    else:
        # 调用者给的是文件夹
        output_gif = output_dir / f"{input_path.stem}.gif"
        output_gif.parent.mkdir(parents=True, exist_ok=True)

    # --- 2) palette 文件 (临时) ---
    palette = output_gif.with_name(f"{input_path.stem}_palette.png")

    # --- 3) 生成 palette ---
    cmd1 = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vf", f"fps={fps},palettegen=max_colors={max_colors}",
        str(palette),
    ]
    subprocess.run(cmd1, check=True)

    # --- 4) 用 palette 合成 GIF ---
    cmd2 = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-i", str(palette),
        "-lavfi", "paletteuse=dither=sierra2_4a",
        "-loop", "0",  # 无限循环
        str(output_gif),
    ]
    print(f"🔄 转换 GIF: {output_gif.name}")
    subprocess.run(cmd2, check=True)

    # --- 5) 清理临时 palette ---
    palette.unlink(missing_ok=True)

    print(f"✔️ 已生成: {output_gif}")
    return f"视频已成功转换为 GIF，保存路径：{output_gif}"


if __name__ == "__main__":
    # 例：python Video_Processing_server.py
    #     然后在别处用 FastMCP 客户端调用 mp4_to_gif_ffmpeg
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8012)