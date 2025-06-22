import streamlit as st
import os

st.markdown("""
<style>
/* 隐藏多页导航那块 */
div[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)



with st.sidebar:
    if st.button("返回主页面"):
        st.switch_page("client.py")



# 取当前脚本文件所在目录
base_dir = os.path.dirname(__file__)
img_path1 = os.path.join(base_dir, "youtube1.png")
img_path2 = os.path.join(base_dir, "youtube2.png")
img_path3 = os.path.join(base_dir, "youtube3.png")
img_path4 = os.path.join(base_dir, "youtube4.png")
img_path5 = os.path.join(base_dir, "youtube5.png")
img_path6 = os.path.join(base_dir, "youtube6.png")
img_path7 = os.path.join(base_dir, "youtube7.png")
img_path8 = os.path.join(base_dir, "youtube8.png")
img_path9 = os.path.join(base_dir, "youtube9.png")
img_path10 = os.path.join(base_dir, "youtube10.png")
img_path11 = os.path.join(base_dir, "youtube11.png")



st.title("youtube api key 获取方法")
st.write("")
st.markdown("#### 1.访问 google cloud 页面")
st.link_button("前往 google cloud", "https://console.cloud.google.com/apis/dashboard?_gl=1*yjxk1v*_up*MQ..&gclid=Cj0KCQjwsNnCBhDRARIsAEzia4AHAXKH9utdLzCbitWFhSQ3YT1otXc_ayEmiSjniMF4PF2-Trw7gaAaAu34EALw_wcB&gclsrc=aw.ds&inv=1&invt=Ab0vYg&project=chatapp-5e029")
st.markdown("如果尚未登录，系统会跳转到 Google 登录页，请用gmail账号登录并完成认证，认证后会自动返回Google Cloud页面。")
st.write("")
st.write("")


st.markdown("#### 2.新建项目")
st.markdown("点击左上角的**Google Cloud**")
st.image(img_path1)
st.markdown("然后页面会刷新一下，就能看到左上角的项目了，点击这个项目")
st.image(img_path2)
st.markdown("点击右上角的新建项目")
st.image(img_path3)
st.markdown("随便起一个项目名字即可，然后点击创建")
st.image(img_path4)
st.markdown("然后继续点击左上角的项目")
st.image(img_path5)
st.markdown("选择刚才创建好的项目。")
st.image(img_path6)
st.write("")
st.write("")



st.markdown("#### 3.创建apikey")
st.markdown("直接去到下面这个网址：")
st.link_button("前往 google cloud", "https://console.cloud.google.com/apis/library/youtube.googleapis.com?authuser=1&inv=1&invt=Ab0vZw&project=virtual-plating-463621-i0")
st.markdown("点击启用")
st.markdown("然后点击左边的凭据")
st.image(img_path7)
st.markdown("然后上方的创建凭据")
st.image(img_path8)
st.markdown("选择api密钥")
st.markdown("关闭以后点击创建好的api密钥名")
st.image(img_path9)
st.markdown("点击限制密钥并在Select APIs 中找到Youtube Data API v3 勾选并保存就好")
st.image(img_path10)
st.markdown("最后点击右边的显示密钥，就能得到API Key了，这个API KEY就是你需要的Youtube API KEY")
st.image(img_path11)




