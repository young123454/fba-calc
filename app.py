import streamlit as st
import math
import requests
import json

# 设置页面，针对手机端优化布局
st.set_page_config(page_title="WY FBA工具", layout="centered")

# --- 1. 获取 Secrets 配置 ---
APP_ID = st.secrets.get("FEISHU_APP_ID")
APP_SECRET = st.secrets.get("FEISHU_APP_SECRET")
APP_TOKEN = st.secrets.get("FEISHU_APP_TOKEN")
TABLE_ID = st.secrets.get("FEISHU_TABLE_ID")

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET})
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=payload)
        return response.json().get("tenant_access_token")
    except:
        return None

# --- 2. 顶部输入区 ---
st.title("📦 WY FBA工具")

sku = st.text_input("请输入 SKU (选填)", placeholder="例如：SKU-2026-001")

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

# --- 3. 核心计算逻辑 ---
w_lb = weight_g / 453.5924
dims_in = sorted([l_cm/2.54, w_cm/2.54, h_cm/2.54], reverse=True)
v_factor = 139 * (2.54**3)
vol_weight = (l_cm * w_cm * h_cm) / v_factor
bill_weight = max(w_lb, vol_weight)

# 判定小号/大号
is_small = (dims_in[0] <= 15 and dims_in[1] <= 12 and dims_in[2] <= 0.75 and w_lb <= 1)
size_tier = "小号标准尺寸" if is_small else "大号标准尺寸"

fee = 0.0
upper_weight = 0.0

if is_small:
    thresholds = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    fees = [3.51, 3.54, 3.59, 3.69, 3.91, 4.09, 4.20, 4.25]
    idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
    fee = fees[idx]
    upper_weight = thresholds[idx]
else:
    # 大号标准尺寸：大于 3 磅用公式，不保留 5 磅特殊值
    if bill_weight > 3.0:
        extra_units = math.ceil(max(0, bill_weight - 3.0) / 0.5)
        fee = extra_units * 0.16 + 6.9 
        upper_weight = 3.0 + (extra_units * 0.5)
    else:
        thresholds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        fees = [4.3, 4.5, 4.72, 5.17, 5.87, 6.04, 6.14, 6.25, 6.6, 6.72, 6.77, 6.9]
        idx = next((i for i, t in enumerate(thresholds) if bill_weight <= t), len(thresholds)-1)
        fee = fees[idx]
        upper_weight = thresholds[idx]

# --- 4. 结论展示 ---
st.divider()
max_h_calc = (upper_weight * v_factor) / (l_cm * w_cm)
final_max_h = min(1.9, max_h_calc) if is_small else max_h_calc

# 绿色结论卡片
st.markdown(f"""
<div style="background-color:#d4edda; padding:15px; border-radius:10px; border-left:5px solid #28a745;">
    <p style="color:#155724; margin:0; font-size:14px;">📏 当前运费档位最大允许高度：</p>
    <p style="color:#155724; margin:0; font-size:28px; font-weight:bold;">{final_max_h:.2f} cm</p>
</div>
""", unsafe_allow_html=True)
st.caption(f"在该高度内，运费维持在 **${fee:.2f}** 不变")

# --- 5. 判定结果与保存按钮 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("判定等级", size_tier)
with col2:
    st.metric("FBA 配送费", f"${fee:.2f}")

if st.button("💾 保存数据到飞书多维表", disabled=not sku):
    token = get_tenant_access_token()
    if not token:
        st.error("获取飞書授权失败，请检查 Secrets 配置。")
    else:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        payload = json.dumps({
            "fields": {
                "SKU": sku,
                "判定等级": size_tier,
                "配送费": fee,
                "最大高度(cm)": round(final_max_h, 2),
                "当前重量(g)": weight_g,
                "长度(cm)": l_cm,
                "宽度(cm)": w_cm
            }
        })
        response = requests.post(url, headers=headers, data=payload)
        if response.json().get("code") == 0:
            st.success("✅ 数据已保存！")
            st.balloons()
        else:
            st.error(f"保存失败：{response.json().get('msg')}")
elif not sku:
    st.warning("⚠️ 请输入 SKU 以激活保存功能。")
