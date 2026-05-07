import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import io

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
    
    **示例：**
    | 日期 | 锐进复刻净值 | 安平锐进净值 | 混吃等死净值 | 清洁能源净值 |
    |------|------------|------------|------------|------------|
    | 2025-11-21 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
    | 2025-12-01 | 1.0046 | 1.0041 | 1.0397 | 1.0469 |
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
    st.error("❌ 未找到净值列！请确保Excel文件中包含'净值'列（如'锐进复刻净值'）")
    st.stop()

# 基金配置（自动识别）
funds = {}
colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for i, col in enumerate(nav_columns):
    fund_name = col.replace('净值', '')
    funds[fund_name] = col

colors = {name: colors_list[i % len(colors_list)] for i, name in enumerate(funds.keys())}

# 侧边栏筛选器
st.sidebar.header("📊 筛选器")

selected_funds = st.sidebar.multiselect(
    "选择基金",
    options=list(funds.keys()),
    default=list(funds.keys())
)

date_range = st.sidebar.date_input(
    "日期范围",
    value=(df['日期'].min(), df['日期'].max()),
    min_value=df['日期'].min(),
    max_value=df['日期'].max()
)

# 筛选数据
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df['日期'] >= pd.Timestamp(start_date)) &amp; amp;
                     (df['日期'] <= pd.Timestamp(end_date))]
else:
    filtered_df = df

# 计算最大回撤
def calc_max_drawdown(nav_series):
    cumulative_max = nav_series.cummax()
    drawdown = (nav_series - cumulative_max) / cumulative_max
    return drawdown.min()

# 数据概览
with st.sidebar.expander("📈 数据概览"):
    st.write(f"**数据期间：**")
    st.write(f"{df['日期'].min().strftime('%Y-%m-%d')} 至 {df['日期'].max().strftime('%Y-%m-%d')}")
    st.write(f"**记录条数：** {len(df)} 条")
    st.write(f"**识别到基金：** {len(funds)} 只")

# 第一行：净值走势 + 收益率对比
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 基金净值走势")
    
    if selected_funds:
        fig_nav = go.Figure()
        for fund in selected_funds:
            nav_col = funds[fund]
            fig_nav.add_trace(go.Scatter(
                x=filtered_df['日期'],
                y=filtered_df[nav_col],
                mode='lines+markers',
                line_shape='spline',
                name=fund,
                line=dict(color=colors[fund], width=2.5),
                marker=dict(size=5),
                hovertemplate='<b>%{fullData.name}</b><br>日期: %{x|%Y-%m-%d}<br>净值: %{y:.4f}<extra></extra>'
            ))
        
        fig_nav.update_layout(
            xaxis_title='日期',
            yaxis_title='净值',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(t=30, b=30, l=40, r=20),
            plot_bgcolor='white',
            yaxis=dict(tickformat='.4f')
        )
        fig_nav.update_xaxes(showgrid=True, gridcolor='#E0E0E0')
        fig_nav.update_yaxes(showgrid=True, gridcolor='#E0E0E0')
        
        st.plotly_chart(fig_nav, use_container_width=True)
    else:
        st.warning("请至少选择一个基金")

with col2:
    st.subheader("📊 收益率对比（%）")
    
    if selected_funds:
        fig_return = go.Figure()
        for fund in selected_funds:
            nav_col = funds[fund]
            returns = (filtered_df[nav_col] / filtered_df[nav_col].iloc[0] - 1) * 100
            
            fig_return.add_trace(go.Scatter(
                x=filtered_df['日期'],
                y=returns,
                mode='lines+markers',
                line_shape='spline',
                name=fund,
                line=dict(color=colors[fund], width=2.5),
                marker=dict(size=5),
                hovertemplate='<b>%{fullData.name}</b><br>日期: %{x|%Y-%m-%d}<br>收益率: %{y:.2f}%<extra></extra>'
            ))
        
        fig_return.update_layout(
            xaxis_title='日期',
            yaxis_title='收益率 (%)',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(t=30, b=30, l=40, r=20),
            plot_bgcolor='white'
        )
        fig_return.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
        fig_return.update_xaxes(showgrid=True, gridcolor='#E0E0E0')
        fig_return.update_yaxes(showgrid=True, gridcolor='#E0E0E0')
        
        st.plotly_chart(fig_return, use_container_width=True)
    else:
        st.warning("请至少选择一个基金")

# 第二行：回撤分析 + 组合总收益
col3, col4 = st.columns(2)

with col3:
    st.subheader("📉 回撤分析（%）")
    
    if selected_funds:
        fig_dd = go.Figure()
        for fund in selected_funds:
            nav_col = funds[fund]
            nav_series = filtered_df[nav_col]
            cumulative_max = nav_series.cummax()
            drawdown = (nav_series - cumulative_max) / cumulative_max * 100
            
            fig_dd.add_trace(go.Scatter(
                x=filtered_df['日期'],
                y=drawdown,
                mode='lines',
                line_shape='spline',
                name=fund,
                line=dict(color=colors[fund], width=2),
                fill='tozeroy',
                fillcolor=colors[fund].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                hovertemplate='<b>%{fullData.name}</b><br>日期: %{x|%Y-%m-%d}<br>回撤: %{y:.2f}%<extra></extra>'
            ))
        
        fig_dd.update_layout(
            xaxis_title='日期',
            yaxis_title='回撤 (%)',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(t=30, b=30, l=40, r=20),
            plot_bgcolor='white'
        )
        fig_dd.update_xaxes(showgrid=True, gridcolor='#E0E0E0')
        fig_dd.update_yaxes(showgrid=True, gridcolor='#E0E0E0')
        
        st.plotly_chart(fig_dd, use_container_width=True)
    else:
        st.warning("请至少选择一个基金")

with col4:
    st.subheader("💼 组合总收益率（等权重%）")
    
    if selected_funds:
        # 计算等权重组合总收益
        portfolio_nav = pd.Series(0, index=filtered_df.index)
        for fund in selected_funds:
            portfolio_nav += filtered_df[funds[fund]]
        portfolio_nav = portfolio_nav / len(selected_funds)
        
        portfolio_return = (portfolio_nav / portfolio_nav.iloc[0] - 1) * 100
        
        fig_port = go.Figure()
        fig_port.add_trace(go.Scatter(
            x=filtered_df['日期'],
            y=portfolio_return,
            mode='lines+markers',
            line_shape='spline',
            name='组合总收益',
            line=dict(color='purple', width=3),
            marker=dict(size=6),
            hovertemplate='<b>组合总收益</b><br>日期: %{x|%Y-%m-%d}<br>收益率: %{y:.2f}%<extra></extra>'
        ))
        
        fig_port.update_layout(
            xaxis_title='日期',
            yaxis_title='收益率 (%)',
            hovermode='x unified',
            height=400,
            margin=dict(t=30, b=30, l=40, r=20),
            plot_bgcolor='white'
        )
        fig_port.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
        fig_port.update_xaxes(showgrid=True, gridcolor='#E0E0E0')
        fig_port.update_yaxes(showgrid=True, gridcolor='#E0E0E0')
        
        st.plotly_chart(fig_port, use_container_width=True)

# 第三行：风险收益指标表格
st.subheader("📋 风险收益指标")

if selected_funds:
    metrics_data = []
    for fund in selected_funds:
        nav_col = funds[fund]
        nav_series = filtered_df[nav_col]
        
        # 总收益率
        total_return = (nav_series.iloc[-1] / nav_series.iloc[0] - 1) * 100
        
        # 年化收益率
        days = (filtered_df['日期'].iloc[-1] - filtered_df['日期'].iloc[0]).days
        if days > 0:
            annual_return = ((1 + total_return/100) ** (365/days) - 1) * 100
        else:
            annual_return = 0
        
        # 波动率
        daily_returns = nav_series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(250) * 100
        
        # 最大回撤
        max_dd = calc_max_drawdown(nav_series) * 100
        
        # 夏普比率
        risk_free = 3.0
        sharpe = (annual_return - risk_free) / volatility if volatility > 0 else 0
        
        # 胜率
        win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100 if len(daily_returns) > 0 else 0
        
        metrics_data.append({
            '基金': fund,
            '总收益率': f'{total_return:.2f}%',
            '年化收益率': f'{annual_return:.2f}%',
            '波动率': f'{volatility:.2f}%',
            '最大回撤': f'{max_dd:.2f}%',
            '夏普比率': f'{sharpe:.2f}',
            '胜率': f'{win_rate:.1f}%'
        })
    
    # 显示表格
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(
        metrics_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("请至少选择一个基金")

# 页脚
st.markdown("---")
st.markdown("**使用说明：** 上传Excel文件 → 选择基金 → 查看分析 | **更新时间**：{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
