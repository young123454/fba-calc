import streamlit as st
import math
import requests
import json

# --- 页面基础配置 ---
st.set_page_config(
    page_title="WY FBA Pro", 
    page_icon="📦", 
    layout="centered"
)

# 自定义 CSS 样式美化
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stMetricValue"] { font-size: 22px !important; color: #1f77b4; }
    .footer { text-align: center; color: #666; font-size: 12px; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

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
    except: return None

# --- 2. 顶部标题区 ---
st.title("📦 WY FBA 智能计算器")
st.caption("集成低价、标准、高价三档费率及飞书自动同步")

# --- 3. 基础信息录入 (SKU与售价区间) ---
with st.expander("📝 基础信息录入", expanded=True):
    sku = st.text_input("产品 SKU", placeholder="请输入或粘贴 SKU 代码")
    # 使用 \$ 转义美元符号，防止被识别为 LaTeX 公式
    price_tier = st.radio(
        "商品售价区间",
        ["<\$10 (低价)", "\$10-\$50 (标准)", ">\$50 (高价)"],
        index=1,
        horizontal=True
    )

# --- 4. 包装规格输入 ---
st.subheader("📏 包装规格")
with st.container():
    col_w, col_l = st.columns(2)
    with col_w:
        weight_g = st.number_input("实重 (g)", value=460.0, step=10.0)
    with col_l:
        l_cm = st.number_input("最长边 (cm)", value=37.5, step=0.1)
    
    col_width, col_h = st.columns(2)
    with col_width:
        w_cm = st.number_input("次长边 (cm)", value=29.5, step=0.1)
    with col_h:
        h_cm = st.number_input("最短边 (cm)", value=1.9, step=0.1)

# --- 5. 核心计算逻辑 ---
w_lb = weight_g / 453.5924
dims_in = sorted([l_cm/2.54, w_cm/2.54, h_cm/2.54], reverse=True)
v_factor = 139 * (2.54**3)
vol_weight = (l_cm * w_cm * h_cm) / v_factor
bill_weight = max(w_lb, vol_weight)

is_small = (dims_in[0] <= 15 and dims_in[1] <= 12 and dims_in[2] <= 0.75 and w_lb <= 1)
size_tier = "小号标准尺寸" if is_small else "大号标准尺寸"

fee, upper_weight = 0.0, 0.0
thresholds_std = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
thresholds_small = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]

# 费率分支判定逻辑
clean_price_tier = price_tier.replace("\\", "") # 去掉转义符用于后续逻辑和显示

if "低价" in clean_price_tier:
    if is_small:
        fees = [2.62, 2.64, 2.68, 2.81, 3.00, 3.10, 3.20, 3.30]
        idx = next((i for i, t in enumerate(thresholds_small) if bill_weight <= t), len(thresholds_small)-1)
        fee, upper_weight = fees[idx], thresholds_small[idx]
    else:
        if bill_weight > 3.0:
            extra_units = math.ceil(max(0, bill_weight - 3.0) / 0.5)
            fee, upper_weight = extra_units * 0.16 + 6.82, 3.0 + (extra_units * 0.5)
        else:
            fees = [3.48, 3.68, 3.90, 4.35, 5.05, 5.22, 5.32, 5.43, 5.78, 5.90, 5.95, 6.08]
            idx = next((i for i, t in enumerate(thresholds_std) if bill_weight <= t), len(thresholds_std)-1)
            fee, upper_weight = fees[idx], thresholds_std[idx]

elif "高价" in clean_price_tier:
    if is_small:
        fees = [3.77, 3.80, 3.85, 3.95, 4.17, 4.35, 4.46, 4.51]
        idx = next((i for i, t in enumerate(thresholds_small) if bill_weight <= t), len(thresholds_small)-1)
        fee, upper_weight = fees[idx], thresholds_small[idx]
    else:
        if bill_weight > 3.0:
            extra_units = math.ceil(max(0, bill_weight - 3.0) / 0.5)
            fee, upper_weight = extra_units * 0.16 + 7.63, 3.0 + (extra_units * 0.5)
        else:
            fees = [4.56, 4.76, 4.98, 5.43, 6.13, 6.30, 6.40, 6.51, 6.86, 6.98, 7.03, 7.16]
            idx = next((i for i, t in enumerate(thresholds_std) if bill_weight <= t), len(thresholds_std)-1)
            fee, upper_weight = fees[idx], thresholds_std[idx]

else: # 标准售价区间
    if is_small:
        fees = [3.51, 3.54, 3.59, 3.69, 3.91, 4.09, 4.20, 4.25]
        idx = next((i for i, t in enumerate(thresholds_small) if bill_weight <= t), len(thresholds_small)-1)
        fee, upper_weight = fees[idx], thresholds_small[idx]
    else:
        if bill_weight > 3.0:
            extra_units = math.ceil(max(0, bill_weight - 3.0) / 0.5)
            fee, upper_weight = extra_units * 0.16 + 6.9, 3.0 + (extra_units * 0.5)
        else:
            fees = [4.3, 4.5, 4.72, 5.17, 5.87, 6.04, 6.14, 6.25, 6.6, 6.72, 6.77, 6.9]
            idx = next((i for i, t in enumerate(thresholds_std) if bill_weight <= t), len(thresholds_std)-1)
            fee, upper_weight = fees[idx], thresholds_std[idx]

# 计算最大高度建议
max_h_calc = (upper_weight * v_factor) / (l_cm * w_cm)
final_max_h = min(1.9, max_h_calc) if is_small else max_h_calc

# --- 6. 核心结果显示 ---
st.divider()
st.subheader("💡 计算结论")
st.success(f"📌 **当前运费档位最大允许高度：{final_max_h:.2f} cm**")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("配送费用", f"${fee:.2f}")
with m2:
    st.metric("计费上限", f"{upper_weight} lb")
with m3:
    st.metric("判定等级", size_tier)

with st.expander("🔍 查看计算细节"):
    st.write(f"- 实重: {w_lb:.3f} lb | 体积重: {vol_weight:.3f} lb")
    st.write(f"- 最终计费重量: {bill_weight:.3f} lb")
    st.write(f"- 对应费用档位: {upper_weight} lb 以下")

# --- 7. 保存到飞书 (修复截断并添加新字段) ---
st.write("")
if st.button("🚀 同步数据至飞书多维表格", use_container_width=True, type="primary", disabled=not sku):
    token = get_tenant_access_token()
    if token:
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
                "宽度(cm)": w_cm, 
                "售价区间": clean_price_tier,
                "计费重量上限(lb)": upper_weight
            }
        })
        try:
            res = requests.post(url, headers=headers, data=payload)
            if res.json().get("code") == 0:
                st.success("🎉 数据已同步至飞书！")
                st.balloons()
            else: st.error(f"同步失败: {res.json().get('msg')}")
        except Exception as e: st.error(f"网络异常: {e}")
    else: st.error("飞书授权失败，请检查 Secrets。")

if not sku:
    st.info("💡 录入 SKU 后即可解锁数据同步功能")

st.markdown('<div class="footer">WY FBA Optimization Tool v2.1</div>', unsafe_allow_html=True)
