import streamlit as st
import math

# 设置页面样式
st.set_page_config(page_title="WEIYUE FBA 运费与高度优化工具", layout="centered")

# --- 侧边栏：输入产品原始参数 ---
with st.sidebar:
    st.header("1. 输入产品参数")
    weight_g = st.number_input("包装实重 (g)", value=460.0, step=10.0)
    l_cm = st.number_input("长度 (cm)", value=37.5, step=0.1)
    w_cm = st.number_input("宽度 (cm)", value=29.5, step=0.1)
    h_cm = st.number_input("高度 (cm)", value=1.9, step=0.1)

st.title("📦 FBA 运费与高度计算专家")

# --- 核心计算逻辑 ---

# 1. 单位转换
w_lb = weight_g / 453.5924
# 将长宽高按英寸排序：[最长, 次长, 最短]
dims_in = sorted([l_cm/2.54, w_cm/2.54, h_cm/2.54], reverse=True)
# 体积重量公式: (长*宽*高) / (139 * 2.54^3)
vol_weight = (l_cm * w_cm * h_cm) / (139 * (2.54**3))
# 计费重量取实重和体积重之大者
bill_weight = max(w_lb, vol_weight)

# 2. 尺寸等级判定
# 小号标准尺寸限制：最长边<=15", 次长边<=12", 最短边<=0.75", 且实重<=1 lb
is_small = (dims_in[0] <= 15 and dims_in[1] <= 12 and 
            dims_in[2] <= 0.75 and w_lb <= 1)
size_tier = "小号标准尺寸" if is_small else "大号标准尺寸"

# 3. 配送费查找逻辑 (基于您最新的费率表)
fee = 0.0
upper_weight = 0.0 # 用于高度反推的档位重量上限

if is_small:
    # 小号标准尺寸费率表
    thresholds = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    fees = [3.51, 3.54, 3.59, 3.69, 3.91, 4.09, 4.20, 4.25]
    
    # 查找匹配档位
    idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
    fee = fees[idx]
    upper_weight = thresholds[idx]
else:
    # 大号标准尺寸费率表
    if bill_weight > 5:
        # 超过 5 磅的公式: (计费重-5)向上取0.5的倍数 * 0.16 + 7.61
        extra_units = math.ceil(max(0, bill_weight - 5) / 0.5)
        fee = extra_units * 0.16 + 7.61
        upper_weight = 5 + (extra_units * 0.5)
    else:
        # 大号 5 磅以内档位
        thresholds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 5.0]
        fees = [4.3, 4.5, 4.72, 5.17, 5.87, 6.04, 6.14, 6.25, 6.6, 6.72, 6.77, 6.9, 7.61]
        
        idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
        fee = fees[idx]
        upper_weight = thresholds[idx]

# --- 结果展示区 ---
st.subheader("判定结果")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("尺寸等级", size_tier)
with col2:
    st.metric("计费重量 (lb)", f"{bill_weight:.3f}")
with col3:
    st.metric("FBA 配送费", f"${fee:.2f}")

st.info(f"💡 当前计费依据：{'实重' if w_lb > vol_weight else '体积重'}")

# --- 高度优化建议 ---
st.divider()
st.subheader("📏 高度优化建议")

# 高度反推公式: 高度 = (重量上限 * 139 * 2.54^3) / (长 * 宽)
# 这里的重量上限是当前运费档位所允许的最大值
v_factor = 139 * (2.54**3)
max_h_calc = (upper_weight * v_factor) / (l_cm * w_cm)

if is_small:
    # 小号尺寸额外受到 1.9cm (0.75") 的硬性物理限制
    final_max_h = min(1.9, max_h_calc)
else:
    final_max_h = max_h_calc

st.success(f"在不增加当前运费 **(${fee:.2f})** 的前提下，你的最大允许高度为：**{final_max_h:.2f} cm**")

# 详细参数比对（可选，用于调试）
with st.expander("查看详细换算参数"):
    st.write(f"- 实重: {w_lb:.4f} lb")
    st.write(f"- 体积重: {vol_weight:.4f} lb")
    st.write(f"- 当前费用档位上限: {upper_weight} lb")
    st.write(f"- 换算常数 (139*2.54^3): {v_factor:.2f}")
