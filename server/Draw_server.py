import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
from fastmcp import FastMCP
from pathlib import Path


mcp = FastMCP("DrawServer")

@mcp.tool()
def draw_image(prompt:str,image_name:str):
    """根据输入的prompt调用模型来生成图片。通常调用完这个工具以后就需要把图片展示到前端。
Params：
    prompt:String,对图片的描述，描述的越细致则图片生成的越精致。prompt最好是英文。
    image_name:String,给即将生成的图片起一个名字，名字必须是**英文**。
Returns:
    String，生成好图片以后会返回图片保存的绝对路径。
    """
    ENV_PATH = Path(__file__).with_name(".env")

    load_dotenv(dotenv_path=ENV_PATH, override=True)


    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    contents = prompt

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(
          response_modalities=['TEXT', 'IMAGE']
        )
    )

    save_dir = r"C:\images"
    os.makedirs(save_dir, exist_ok=True)

    save_path =f"C:\\images\\{image_name}.png"

    # WSL2 下 C 盘挂载在 /mnt/c
    # save_dir = "/mnt/c/images"
    # os.makedirs(save_dir, exist_ok=True)
    #
    # # 用 Linux 风格的斜杠拼接路径
    # save_path = f"{save_dir}/{image_name}.png"


    for part in response.candidates[0].content.parts:
      # if part.text is not None:
      #   print(part.text)
      if part.inline_data is not None:
        image = Image.open(BytesIO((part.inline_data.data)))
        image.save(save_path)

    return f"图片已经保存到:{save_path}"


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8006)