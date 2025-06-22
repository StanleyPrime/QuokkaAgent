import os
import requests
from fastmcp import FastMCP
import json
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=True)


mcp = FastMCP(name="AmapServer")


@mcp.tool()
def keyword_search(keywords:str,city:str):
    """
    使用高德地图API根据关键字和城市进行地点搜索。

    Args:
        keywords (str): 要搜索的关键字，例如 "麦当劳" 或 "公园"。
        city (str): 要搜索的城市，例如 "北京"。

    Returns:
        str: 包含所有搜索结果的格式化字符串。如果HTTP请求失败，则返回错误信息。
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)


    key = os.getenv("AMAP_API_KEY")
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={keywords}&city={city}"

    response = requests.get(url)

    final_text = ""

    if response.status_code == 200:
        # 将返回的 JSON 数据转换成 Python 字典
        data = response.json()
        for poi in data["pois"]:
            star = "-"*30
            name = f"名称: {poi['name']}"
            address = f"地址: {poi['address']}"
            open_time = f"开放时间: {poi['biz_ext']['opentime2']}"
            rate = f"评分: {poi['biz_ext']['rating']}"
            final_text += f"{star}\n{name}\n{address}\n{open_time}\n{rate}\n"

        # print(final_text)
        return final_text
    else:
        return f"HTTP 请求失败: {response.status_code}"


def get_location_coordinate(address: str):
    """
    使用高德地理编码API将地址转换为经纬度坐标。

    Args:
        address (str): 需要查询的地址。

    Returns:
        str: "经度,纬度" 格式的坐标字符串，如果失败则返回 None。
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    key = os.getenv("AMAP_API_KEY")

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {'key': key, 'address': address}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == '1' and data.get('geocodes'):
            return data['geocodes'][0]['location']
        else:
            print(f"地址 '{address}' 解析失败: {data.get('info')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"地理编码请求失败: {e}")
        return None


@mcp.tool()
def get_amap_driving_route(origin_place, destination_place,strategy=0, extensions='base'):
    """
    调用高德地图驾车路线规划API获取到规划驾车路线的相关信息。

    Args:
        origin_place (str): 起点位置，比如"北京天安门"。
        destination_place (str): 终点位置，比如"北京故宫"。
        strategy (int, optional): 路线规划策略。默认为 0 (速度优先)。
                                  0: 速度优先
                                  1: 费用优先
                                  2: 时间优先
                                  3: 距离优先
                                  4: 不走高速
                                  5: 避免收费
                                  6: 避免拥堵
                                  7: 多策略
        extensions (str, optional): 返回结果的详细程度。'base' (默认) 或 'all'。

    Returns:
        string:里面包含总距离，预计耗时，途径红绿灯，过路费，导航路线的详细规划的信息
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    api_key= os.getenv("AMAP_API_KEY")

    url = "https://restapi.amap.com/v3/direction/driving"

    origin = get_location_coordinate(origin_place)
    destination = get_location_coordinate(destination_place)

    # 构建请求参数
    params = {
        "key": api_key,
        "origin": origin,
        "destination": destination,
        "strategy": strategy,
        "extensions": extensions
    }

    try:
        # 发送GET请求
        response = requests.get(url, params=params)

        # 检查HTTP响应状态码，如果不是2xx，则抛出异常
        response.raise_for_status()

        # 解析JSON响应
        data = response.json()

        # 检查高德API返回的状态码
        if data and data.get("status") == "1" and data["route"]["paths"]:
            route = data["route"]["paths"][0]  # 通常取第一条路径（最佳路径）

            total_distance_km = float(route["distance"]) / 1000
            total_duration_minutes = float(route["duration"]) / 60
            taxi_cost = data["route"].get("taxi_cost", "未知")

            final_data = f'''
--- 驾车路线概览 ---
总距离: {total_distance_km:.2f} 公里
预计耗时: {total_duration_minutes:.0f} 分钟
途经红绿灯: {route.get('traffic_lights', 'N/A')} 个
过路费: {route['tolls']} 元
打车费用预估: {taxi_cost} 元
\n--- 详细导航步骤 ---
'''
            steps_text = f""
            for i, current_step_data in enumerate(route["steps"]):  # 将循环变量改为 current_step_data，避免与外部的 `steps_text` 混淆
                instruction = current_step_data["instruction"]
                road_name = current_step_data.get("road", "未知道路")
                step_distance_m = float(current_step_data["distance"])
                step_duration_s = float(current_step_data["duration"])

                if step_distance_m > 10:
                    steps_text += f"\n  {i + 1}. {instruction} (沿 '{road_name}' 行驶 {step_distance_m:.0f} 米, 约 {step_duration_s:.0f} 秒)"
                else:
                    steps_text += f"\n  {i + 1}. {instruction}"

            final_data += steps_text  # 将累积的步骤文本添加到最终数据中
            return final_data
        else:
            return f"未能成功获取驾车路线信息或数据格式不正确。高德API信息: {data.get('info', '无具体信息')}"

    except requests.exceptions.RequestException as e:
        print(f"请求发生网络或HTTP错误: {e}")
        return None
    except json.JSONDecodeError:
        print("无法解析JSON响应。")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None


@mcp.tool()
def get_amap_transit_route(origin_place,destination_place,city:str,strategy=0,extensions='base'):
    """
    调用高德地图公交路线规划API来规划如何乘坐公交车或者地铁到指定地点
    Args:
        origin_place (str): 起点位置，比如"北京天安门"。
        destination_place (str): 终点位置，比如"北京故宫"。
        city (str): 必需。进行公交规划的城市名称或城市编码。
        strategy (int, optional): 路线规划策略。默认为 0 (速度优先)。
                                  0: 速度优先
                                  1: 费用优先
                                  2: 时间优先
                                  3: 距离优先
                                  4: 不走高速
                                  5: 避免收费
                                  6: 避免拥堵
                                  7: 多策略
        extensions (str, optional): 返回结果的详细程度。'base' (默认) 或 'all'。
    Returns:
        string:返回多条公交路线规划的方案结果
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    api_key = os.getenv("AMAP_API_KEY")

    url = "https://restapi.amap.com/v3/direction/transit/integrated"

    origin = get_location_coordinate(origin_place)
    destination = get_location_coordinate(destination_place)

    # 构建请求参数
    params = {
        "key": api_key,
        "origin": origin,
        "destination": destination,
        "city":city,
        "strategy": strategy,
        "extensions": extensions
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    route_data = response.json()

    if route_data.get("status") == "1":
        final_text = f""
        transits = route_data["route"]["transits"]

        final_text += f'''
--- 公交路线规划结果 ---
共找到 {len(transits)} 条公交方案。
'''
        for i, transit in enumerate(transits):
            final_text += f"\n--- 方案 {i + 1} ---"
            duration_minutes = float(transit["duration"]) / 60
            walking_distance_meters = float(transit["walking_distance"])
            cost = transit.get("cost", "N/A")  # 公交费用可能没有或为0

            final_text += f"\n  预计耗时: {duration_minutes:.0f} 分钟"
            final_text += f"\n  步行距离: {walking_distance_meters:.0f} 米"
            final_text += f"\n  票价: {cost} 元"
            final_text += f"\n  换乘次数: {len(transit['segments']) - 1} 次"
            final_text +=f"\n  详细换乘步骤:"

            for j, segment in enumerate(transit["segments"]):
                if segment["walking"] and float(segment["walking"]["distance"]) > 0:
                    final_text += f"\n    {j + 1}. 步行 {float(segment['walking']['distance']):.0f} 米"

                    # 重要的修改：在访问 buslines[0] 之前，先检查 buslines 列表是否为空
                if segment["bus"] and len(segment["bus"]["buslines"]) > 0:
                    # print(segment["bus"]["buslines"]) # 这行调试代码可以在问题解决后移除
                    # 打印公交线路信息
                    busline = segment["bus"]["buslines"][0]  # 通常只取第一条公交线路信息
                    start_stop = busline["departure_stop"]["name"]
                    end_stop = busline["arrival_stop"]["name"]
                    line_name = busline["name"].replace("(开往", " (开往").replace(")", ")")  # 格式化线路名称

                    final_text += f"\n    {j + 1}. 乘坐 {line_name}，从 '{start_stop}' 站 到 '{end_stop}' 站"
                elif segment["railway"]:
                    pass

        return final_text
    else:
        return f"高德API返回错误：{route_data.get('info', '未知错误')}"


if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002)
