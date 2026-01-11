import streamlit as st
import math

# 设置页面
st.set_page_config(page_title="FBA 运费优化器", layout="centered")
st.title("📦 FBA 运费与高度计算应用")

# --- 侧边栏输入 ---
with st.sidebar:
    st.header("1. 输入产品参数")
    weight_g = st.number_input("包装重量 (g)", value=300.0, step=10.0)
    l_cm = st.number_input("长 (cm)", value=37.5, step=0.1)
    w_cm = st.number_input("宽 (cm)", value=29.5, step=0.1)
    h_cm = st.number_input("高 (cm)", value=1.9, step=0.1)

# --- 核心逻辑计算 ---
# 1. 单位转换
w_lb = weight_g / 453.5924
dims_in = sorted([l_cm/2.54, w_cm/2.54, h_cm/2.54], reverse=True) # [长, 宽, 高] 的英寸排序
vol_weight = (l_cm * w_cm * h_cm) / (139 * (2.54**3))
bill_weight = max(w_lb, vol_weight)

# 2. 尺寸等级判定 (最长15, 次长12, 最短0.75, 重量<=1)
is_small = (dims_in[0] <= 15 and dims_in[1] <= 12 and 
            dims_in[2] <= 0.75 and w_lb <= 1)
size_tier = "小号标准尺寸" if is_small else "大号标准尺寸"

# 3. 费用查找逻辑
fee = 0.0
if is_small:
    # 模拟 Sheet1 C1:J2 数据
    thresholds = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    fees = [3.51, 3.54, 3.59, 3.69, 3.91, 4.09, 4.20, 4.25]
    fee = next((f for t, f in zip(thresholds, fees) if bill_weight <= t), 4.25)
else:
    if bill_weight > 3:
        # 大号超重公式：(F2-3)取0.5倍数 * 0.16 + 6.97
        fee = math.ceil((bill_weight - 3) / 0.5) * 0.16 + 6.97
    else:
        # 模拟 Sheet1 C4:O5 数据
        thresholds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        fees = [4.3, 4.5, 4.72, 5.17, 5.87, 6.04, 6.14, 6.25, 6.6, 6.72, 6.77, 6.9]
        fee = next((f for t, f in zip(thresholds, fees) if bill_weight <= t), 6.9)

# --- 结果展示 ---
st.subheader("判定结果")
c1, c2, c3 = st.columns(3)
c1.metric("尺寸等级", size_tier)
c2.metric("计费重量", f"{bill_weight:.3f} lb")
c3.metric("FBA 配送费", f"${fee:.2f}")

# --- 最大高度反推 ---
st.divider()
st.subheader("💡 优化建议：最大允许高度")
# 反推公式: H = (Weight * 139 * 2.54^3) / (L * W)
max_h_vol = (bill_weight * 139 * (2.54**3)) / (l_cm * w_cm)
if is_small:
    final_max_h = min(1.9, max_h_vol)
else:
    final_max_h = max_h_vol

st.success(f"在不增加当前运费的前提下，你的最大包装高度为：**{final_max_h:.2f} cm**")
if is_small and final_max_h >= 1.9:
    st.caption("注：已受限于小号标准尺寸 1.9cm (0.75in) 的硬性规定")
