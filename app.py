import streamlit as st
import math

# 设置页面，针对手机端优化布局
st.set_page_config(page_title="FBA优化工具", layout="centered")

# --- 1. 顶部输入区 (手机端直接可见) ---
st.title("📦 WY FBA 运费与高度优化工具")

# 使用 columns 将输入框并排，节省垂直空间
with st.container():
    col_w, col_l = st.columns(2)
    with col_w:
        weight_g = st.number_input("包装实重 (g)", value=460.0, step=10.0)
    with col_l:
        l_cm = st.number_input("长度 (cm)", value=37.5, step=0.1)
    
    col_width, col_h = st.columns(2)
    with col_width:
        w_cm = st.number_input("宽度 (cm)", value=29.5, step=0.1)
    with col_h:
        h_cm = st.number_input("高度 (cm)", value=1.9, step=0.1)

# --- 2. 核心逻辑计算 ---
w_lb = weight_g / 453.5924
dims_in = sorted([l_cm/2.54, w_cm/2.54, h_cm/2.54], reverse=True)
v_factor = 139 * (2.54**3) # 约 2277.8
vol_weight = (l_cm * w_cm * h_cm) / v_factor
bill_weight = max(w_lb, vol_weight)

# 尺寸判定
is_small = (dims_in[0] <= 15 and dims_in[1] <= 12 and dims_in[2] <= 0.75 and w_lb <= 1)
size_tier = "小号标准尺寸" if is_small else "大号标准尺寸"

# 费用查找与档位上限捕捉
fee = 0.0
upper_weight = 0.0

if is_small:
    thresholds = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    fees = [3.51, 3.54, 3.59, 3.69, 3.91, 4.09, 4.20, 4.25]
    idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
    fee = fees[idx]
    upper_weight = thresholds[idx]
else:
    if bill_weight > 3:
        extra_units = math.ceil(max(0, bill_weight - 3) / 0.5)
        fee = extra_units * 0.16 + 7.61
        upper_weight = 3 + (extra_units * 0.5)
    else:
        thresholds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        fees = [4.3, 4.5, 4.72, 5.17, 5.87, 6.04, 6.14, 6.25, 6.6, 6.72, 6.77, 6.9]
        idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
        fee = fees[idx]
        upper_weight = thresholds[idx]

# --- 3. 核心结论区 (紧跟输入框) ---
st.divider()
# 重点：将最大高度建议提前到结果最上方
max_h_calc = (upper_weight * v_factor) / (l_cm * w_cm)
final_max_h = min(1.9, max_h_calc) if is_small else max_h_calc

st.success(f"📏 当前档位最大允许高度：**{final_max_h:.2f} cm**")
st.caption(f"在该高度内，运费维持在 **${fee:.2f}** 不变")

# --- 4. 判定详细结果 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("判定等级", size_tier)
with col2:
    st.metric("FBA 配送费", f"${fee:.2f}")

st.info(f"计费重量: {bill_weight:.3f} lb | 依据: {'实重' if w_lb > vol_weight else '体积重'}")

# 隐藏不常用的详细换算
with st.expander("查看详细技术参数"):
    st.write(f"- 实重: {w_lb:.4f} lb")
    st.write(f"- 体积重: {vol_weight:.4f} lb")
    st.write(f"- 匹配档位上限: {upper_weight} lb")
