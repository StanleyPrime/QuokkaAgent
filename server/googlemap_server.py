from dotenv import load_dotenv
import os
import requests
from fastmcp import FastMCP
from pathlib import Path

ENV_PATH = Path(__file__).parent.with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=False)

mcp = FastMCP(name="GoogleMapServer")

@mcp.tool()
def query_search(TextQuery:str):
    """文本搜索谷歌地图信息
        输入想要查询的文本信息，比如‘温哥华列治文的麦当劳餐厅’
        函数就能返回得到Json格式的所有相关地点的相关信息，地点信息包括：formattedAddress,location(坐标),websiteUri,currentOpeningHours,postalAddress，PriceRange内容。
        如果发生错误返回的信息就是‘请求失败’
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    # 1. 准备请求的 URL
    url = "https://places.googleapis.com/v1/places:searchText"

    # 2. 获取 API_KEY（也可以直接写在字符串里，但建议用环境变量保护）
    api_key = os.getenv("GOOGLEMAP_API_KEY")

    # 3. 构造请求头
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # 如果你只想拿部分字段，可以在 FieldMask 里指定
        "X-Goog-FieldMask": ("places.displayName,places.formattedAddress,"
                             "places.location,places.postalAddress,"
                             "places.currentOpeningHours,"
                             "places.websiteUri,places.priceRange"),
    }

    # 4. 构造请求体
    payload = {
        "textQuery": TextQuery,
        "languageCode":"zh",
        "pageSize":4
    }

    # 5. 发送 POST 请求
    response = requests.post(url, headers=headers, json=payload)

    # 6. 检查并处理响应
    if response.status_code == 200:
        result = response.json()
        # 这里根据实际需要处理 result，比如打印或提取信息
        # print("查询结果：", result)
        return result
    else:
        # print(f"请求失败（{response.status_code}），返回信息：{response.text}")
        return "请求失败"




if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)

