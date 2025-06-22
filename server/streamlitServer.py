import streamlit as st
from fastmcp import FastMCP
import os

mcp = FastMCP("StreamlitServer")


@mcp.tool()
def show_image_frontend(image_path:str):
    """
    将路径中的png或jpg等图片格式的文件通过streamlit模块将图片显示到前端给用户看
    Params:
        image_path:String,图片的绝对路径，比如: r"C:\\Users\\85321\\OneDrive\\图片\\屏幕快照\\1.png"
    """
    # st.image(image_path)
    return "图片展示成功"


@mcp.tool()
def show_video_frontend(video_path:str):
    """
    将路径中的.mp4的视频格式的文件通过streamlit模块将视频展示到前端给用户看,url的话只支持youtube链接比如"https://www.youtube.com/watch?v=Stm3EiJaCH4"
    其他的链接是不行的比如bilibili的url就不行！
    Params:
        video_path:String,可以是youtube的url链接(只能是youtube的url)，也可以是一个.mp4视频文件的绝对路径，比如：r"C:\\24.mp4"
    """
    return "视频展示成功"


@mcp.tool()
def show_dataframe_frontend(dataframe_path:str):
    """
    将路径中的.csv或.xlsx格式的文件通过streamlit通过streamlit模块将表格展示到前端给用户看。
    Params:
        dataframe_path:String,.csv或者.xlsx格式文件的绝对路径，比如:r"C:\\24.csv"
    """
    return "表格展示成功"



if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8008)