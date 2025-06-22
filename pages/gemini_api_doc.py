import streamlit as st
import os

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


# 取当前脚本文件所在目录
base_dir = os.path.dirname(__file__)
img_path = os.path.join(base_dir, "firststep.png")


st.title("Google API key 获取方法")
st.write("")
st.markdown("#### 1.访问 AI Studio API Key 页面")
st.link_button("前往 AI Studio", "https://aistudio.google.com/app/apikey")
st.markdown("如果尚未登录，系统会跳转到 Google 登录页，请用gmail账号登录并完成认证，认证后会自动返回AI Studio页面。")
st.write("")
st.write("")

st.markdown("#### 2.注册apikey")
st.markdown("点击右上角的**创建api密钥**")
st.image(img_path)
st.markdown("接下来系统会提示您在现有项目或新项目中生成 API Key。")
st.write("")
st.write("")

st.markdown("#### 3.获取到apikey并保存")
st.markdown("生成后请立即复制并妥善保存，复制到主页面中的gemini api key输入框中并保存即可。")