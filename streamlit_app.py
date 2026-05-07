import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="基金组合分析仪表板",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 基金组合分析仪表板")

# 侧边栏 - 文件上传
st.sidebar.header("📂 数据上传")

uploaded_file = st.sidebar.file_uploader(
    "上传基金净值Excel文件",
    type=['xlsx', 'xls'],
    help="Excel文件需包含：日期列 + 各基金净值列"
)

# 示例数据格式说明
with st.sidebar.expander("📋 查看数据格式要求"):
    st.write("""
    **Excel文件格式要求：**
    - 第1列：日期（格式：YYYY-MM-DD）
    - 第2-5列：各基金净值（如：锐进复刻净值、安平锐进净值等）
    """)

# 加载数据
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期').reset_index(drop=True)
        return df
    return None

df = load_data(uploaded_file)

if df is None:
    st.info("👈 请在左侧上传基金净值Excel文件开始分析")
    st.stop()

# 自动识别基金列（包含"净值"的列）
nav_columns = [col for col in df.columns if '净值' in col]

if len(nav_columns) == 0:
    st.error("❌ 未找到净值列！请确保Excel文件中包含'净值'列")
    st.stop()

# 基金配置
funds = {}
colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for i, col in enumerate(nav_columns):
    fund_name = col.replace('净值', '')
    funds[fund_name] = col

colors = {name: colors_list[i % len(colors_list)] for i, name in enumerate
