from dotenv import load_dotenv
import os
import requests
from fastmcp import FastMCP
from pathlib import Path

ENV_PATH = Path(__file__).parent.with_name(".env")   # 100% 指向当前脚本所在目录

load_dotenv(dotenv_path=ENV_PATH, override=False)

mcp = FastMCP(name="CoinMarketCap_Server")

@mcp.tool()
def get_cryptos_data(limit:str="20"):
    """
    获取虚拟货币相关的数据。
    Param：
        limit:string(默认20),虚拟货币的类别个数，如过是10的话就是获取排名前十的虚拟货币的所有相关数据。
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    # api_key = "2cc6b404-194c-47fb-8a1a-fd524a8d4966"
    api_key = os.getenv("COINMARKETCAP_API_KEY")
    BASE_URL = 'https://pro-api.coinmarketcap.com'
    ENDPOINT = '/v1/cryptocurrency/listings/latest'
    URL = f"{BASE_URL}{ENDPOINT}"

    HEADERS = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
        'Accept-Encoding': 'deflate, gzip'  # 建议添加，用于接收压缩数据以提高效率
    }

    PARAMETERS = {
        'start': '1',
        'limit': limit,  # 获取前 10 条数据
        'convert': 'USD'  # 将价格转换为美元
    }

    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get(URL, params=PARAMETERS)
    response.raise_for_status()
    data = response.json()

    formated_data = f""
    if 'data' in data and len(data['data']) > 0:
        formated_data += f"\n--- 前 {limit} 种真实加密货币概览 ---"
        for i, crypto in enumerate(data['data']):
            formated_data += f"\n  {i+1}. 名称: {crypto['name']} ({crypto['symbol']})"
            formated_data += f"\n     CMC 排名: {crypto['cmc_rank']}"
            formated_data += f"\n     最大供应量: {crypto['max_supply']}"
            formated_data += f"\n     流通供应量: {crypto['circulating_supply']}"
            formated_data += f"\n     总供应量: {crypto['total_supply']}"
            formated_data += f"\n     交易对数量: {crypto['num_market_pairs']}"
            if 'quote' in crypto and 'USD' in crypto['quote']:
                formated_data += f"\n     当前价格 (USD): ${crypto['quote']['USD']['price']:.4f}"
                formated_data += f"\n     24小时交易量: {crypto['quote']['USD']['volume_24h']:.4f}"
                formated_data += f"\n     24小时交易量变化: {crypto['quote']['USD']['volume_change_24h']:.4f}%"
                formated_data += f"\n     1小时价格变化: {crypto['quote']['USD']['percent_change_1h']:.2f}%"
                formated_data += f"\n     24小时价格变化: {crypto['quote']['USD']['percent_change_24h']:.2f}%"
                formated_data += f"\n     7天价格变化: {crypto['quote']['USD']['percent_change_7d']:.2f}%"
                formated_data += f"\n     30天价格变化: {crypto['quote']['USD']['percent_change_30d']:.2f}%"
                formated_data += f"\n     60天价格变化: {crypto['quote']['USD']['percent_change_60d']:.2f}%"
                formated_data += f"\n     90天价格变化: {crypto['quote']['USD']['percent_change_90d']:.2f}%"
                formated_data += f"\n     市值: ${crypto['quote']['USD']['market_cap']:.4f}"
                formated_data += f"\n     市值占有率: {crypto['quote']['USD']['market_cap_dominance']:.4f}%"
                formated_data += f"\n     完全稀释市值: ${crypto['quote']['USD']['fully_diluted_market_cap']:.4f}"
                formated_data += f"\n------------------------------------------------------------------"
        return formated_data
    else:
        return "获取数据失败了。"


@mcp.tool()
def get_specify_crypto(symbol:str):
    """
    获取指定的一种虚拟货币的信息。
    params:
        symbol:string,想查询的加密货币符号,比如：BTC
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    API_KEY = '2cc6b404-194c-47fb-8a1a-fd524a8d4966'

    BASE_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    parameters = {
        'symbol': symbol,
        'convert': 'USD'
    }

    response = requests.get(BASE_URL, headers=headers, params=parameters)
    response.raise_for_status()

    data = response.json()

    formated_data = f""

    formated_data += f"\n--- {symbol}最新数据 ---"

    if symbol in data['data']:
        btc_data = data['data'][symbol]
        btc_quote = btc_data['quote']['USD']
        formated_data += f"\n名称: {btc_data['name']}"
        formated_data += f"\nCMC 排名:{btc_data['cmc_rank']}"
        formated_data += f"\n交易对数量:{btc_data['num_market_pairs']}"
        formated_data += f"\n最大供应量:{btc_data['max_supply']}"
        formated_data += f"\n流通供应量:{btc_data['circulating_supply']}"
        formated_data += f"\n总供应量:{btc_data['total_supply']}"
        formated_data += f"\n当前价格 (USD): ${btc_quote['price']:.2f}"
        formated_data += f"\n24小时交易量:{btc_quote['volume_24h']:.4f}"
        formated_data += f"\n24小时交易量变化: {btc_quote['volume_change_24h']:.4f}%"
        formated_data += f"\n1小时价格变化:{btc_quote['percent_change_1h']}%"
        formated_data += f"\n24小时价格变化:{btc_quote['percent_change_24h']}%"
        formated_data += f"\n7天价格变化:{btc_quote['percent_change_7d']}%"
        formated_data += f"\n30天价格变化:{btc_quote['percent_change_30d']}%"
        formated_data += f"\n60天价格变化:{btc_quote['percent_change_60d']}%"
        formated_data += f"\n90天价格变化:{btc_quote['percent_change_90d']}%"
        formated_data += f"\n市值:${btc_quote['market_cap']}"
        formated_data += f"\n市值占有率:{btc_quote['market_cap_dominance']}%"
        formated_data += f"\n完全稀释市值:${btc_quote['fully_diluted_market_cap']}"

    return formated_data





if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8005)
