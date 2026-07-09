import streamlit as st

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและสวยงาม
st.set_page_config(
    page_title="Pallet & Weight Optimizer", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 Pallet Container Layout & Weight Optimizer")
st.write("เครื่องมือคำนวณการจัดวางและตรวจสอบน้ำหนักพาเลทในตู้คอนเทนเนอร์ (NPI Safety Compliant)")

# --- SIDEBAR INPUTS (แถบเมนูด้านซ้าย) ---
st.sidebar.header("1. ข้อมูลพาเลท (cm & kg)")
p_w = st.sidebar.number_input("ความกว้างพาเลท (Width)", value=80.0, step=5.0)
p_l = st.sidebar.number_input("ความยาวพาเลท (Length)", value=120.0, step=5.0)
p_weight = st.sidebar.number_input("น้ำหนักต่อ 1 พาเลท (kg)", value=500.0, step=50.0)

st.sidebar.header("2. ข้อมูลตู้คอนเทนเนอร์")
c_type = st.sidebar.selectbox("ประเภทตู้", ["20ft", "40ft"])
c_w_raw = 235.0
c_l_raw = 590.0 if c_type == "20ft" else 1203.0

# กำหนดค่าน้ำหนักบรรทุกสูงสุดตามมาตรฐานตู้ (Max Payload)
max_payload = 21500.0 if c_type == "20ft" else 26500.0
st.sidebar.info(f"⚖️ น้ำหนักบรรทุกสูงสุดของตู้ {c_type}: {max_payload:,.0f} kg")

st.sidebar.header("3. ระยะเผื่อความปลอดภัย (Clearance)")
c_w_gap = st.sidebar.slider("ระยะเผื่อด้านกว้าง (Total W)", 0.0, 20.0, 5.0)
c_l_gap = st.sidebar.slider("ระยะเผื่อด้านยาว (Total L)", 0.0, 30.0, 10.0)

# --- CALCULATION LOGIC (ระบบคำนวณ) ---
def solve_layout(pw, pl, cw_raw, cl_raw, cw_clear, cl_clear):
    cw, cl = cw_raw - cw_clear, cl_raw - cl_clear
    
    # 1. คำนวณแบบแถวตรงปกติ (Simple Grid)
    o1 = (cw // pw) * (cl // pl)
    o2 = (cw // pl) * (cl // pw)
    if o1 >= o2:
        simple = {"n_rows": int(cw // pw), "n_type_w": pw, "n_type_l": pl, "n_per_row": int(cl // pl), "m_rows": 0, "total": int(o1)}
    else:
        simple = {"n_rows": int(cw // pl), "n_type_w": pl, "n_type_l": pw, "n_per_row": int(cl // pw), "m_rows": 0, "total": int(o2)}

    # 2. คำนวณแบบผสมแนวตั้ง-แนวนอน (Mixed Orientation)
    best_mixed = {"total": 0}
    for n in range(int(cw // pw) + 1):
        m = int((cw - (n * pw)) // pl)
        total = (n * (cl // pl)) + (m * (cl // pw))
        if total > best_mixed["total"]:
            best_mixed = {"n_rows": n, "n_type_w": pw, "n_type_l": pl, "n_per_row": int(cl // pl), "m_rows": m, "m_type_w": pl, "m_type_l": pw, "m_per_row": int(cl // pw), "total": int(total)}
    return simple, best_mixed

# --- SVG PLOTTING ENGINE (ระบบวาดรูปกราฟิก) ---
def generate_svg_plot(res, title):
    view_box_w = c_l_raw
    view_box_h = c_w_raw
    
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {view_box_w} {view_box_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 3px solid #1e293b; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">'
    svg += f'<rect x="0" y="0" width="{c_l_raw}" height="{c_w_raw}" fill="#f8fafc" stroke="#1e293b" stroke-width="4" />'
    
    usable_l = c_l_raw - c_l_gap
    usable_w = c_w_raw - c_w_gap
    svg += f'<rect x="{c_l_gap/2}" y="{c_w_gap/2}" width="{usable_l}" height="{usable_w}" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6,6" />'
    
    used_w = (res["n_rows"] * res["n_type_w"]) + (res.get("m_rows", 0) * res.get("m_type_w", 0))
    curr_y = (c_w_raw - used_w) / 2
    
    def draw_pallet_group(n_rows, n_per_row, pw, pl, start_y):
        y = start_y
        rects_html = ""
        for i in range(n_rows):
            off_x = (c_l_raw - (n_per_row * pl)) / 2
            for j in range(n_per_row):
                px = off_x + (j * pl)
                py = y
                rects_html += f'<rect x="{px}" y="{py}" width="{pl}" height="{pw}" fill="#bae6fd" stroke="#0284c7" stroke-width="1.5" rx="3" ry="3" />'
                rects_html += f'<text x="{px + (pl/2)}" y="{py + (pw/2) + 5}" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" fill="#0369a1" text-anchor="middle">{int(pl)}x{int(pw)}</text>'
            y += pw
        return y, rects_html

    next_y, g1_html = draw_pallet_group(res["n_rows"], res["n_per_row"], res["n_type_w"], res["n_type_l"], curr_y)
    svg += g1_html
    
    if res.get("m_rows", 0) > 0:
        _, g2_html = draw_pallet_group(res["m_rows"], res["m_per_row"], res["m_type_w"], res["m_type_l"], next_y)
        svg += g2_html
        
    svg += '</svg>'
    return svg

# --- EXECUTION & DISPLAY (ประมวลผลและแสดงผลลัพธ์) ---
simple_res, mixed_res = solve_layout(p_w, p_l, c_w_raw, c_l_raw, c_w_gap, c_l_gap)

col1, col2 = st.columns(2)

# ฟังก์ชันตัวช่วยแสดงผลลัพธ์การคำนวณและเช็คน้ำหนักในแต่ละ Column
def render_result_column(res, title, svg_name):
    st.subheader(title)
    st.metric(label="จำนวนพาเลทที่วางตามพื้นที่ได้", value=f"{res['total']} ใบ")
    
    # คำนวณน้ำหนักรวมของเลย์เอาต์นี้
    total_weight = res['total'] * p_weight
    
    # เช็คเงื่อนไขน้ำหนักเกินพิกัดตู้
    if total_weight > max_payload:
        st.error(f"❌ **น้ำหนักเกินพิกัดตู้!** ({total_weight:,.1f} kg / Max: {max_payload:,.0f} kg)")
        # คำนวณหาจำนวนพาเลทสูงสุดที่ใส่ได้จริงตามเกณฑ์น้ำหนัก
        max_allowed_pallets = int(max_payload // p_weight)
        st.warning(f"⚠️ **คำแนะนำ:** เพื่อความปลอดภัย ควรส่งได้มากที่สุดไม่เกิน **{max_allowed_pallets} พาเลท**")
    else:
        st.success(f"✅ **น้ำหนักปลอดภัยผ่านเกณฑ์** ({total_weight:,.1f} kg / Max: {max_payload:,.0f} kg)")
        
    st.write(generate_svg_plot(res, svg_name), unsafe_allow_html=True)

with col1:
    render_result_column(simple_res, "💡 แบบที่ 1: จัดเรียงแบบปกติ (Simple Grid)", "Simple Grid")

with col2:
    render_result_column(mixed_res, "⚡ แบบที่ 2: จัดเรียงแบบผสมทิศทาง (Mixed)", "Mixed Orientation")

# --- SUMMARY RECOMMENDATION (คำแนะนำภาพรวมด้านล่าง) ---
st.markdown("---")
# หาแบบที่ได้จำนวนพาเลทสูงสุดภายใต้เงื่อนไขน้ำหนักไม่เกิน
valid_simple = simple_res['total'] if (simple_res['total'] * p_weight) <= max_payload else int(max_payload // p_weight)
valid_mixed = mixed_res['total'] if (mixed_res['total'] * p_weight) <= max_payload else int(max_payload // p_weight)

if (mixed_res['total'] * p_weight) > max_payload and (simple_res['total'] * p_weight) > max_payload:
    st.error("🚨 แจ้งเตือน: ขณะนี้น้ำหนักสินค้าเกินพิกัดตู้ทั้งสองรูปแบบการจัดวาง! โปรดลดจำนวนโหลดสินค้าลงตามคำแนะนำด้านบน")
elif mixed_res['total'] > simple_res['total'] and (mixed_res['total'] * p_weight) <= max_payload:
    st.success(f"🔥 แนะนำให้เลือกจัดวางแบบที่ 2 (แบบผสม) เพราะสามารถจุพาเลทเพิ่มได้อีก {mixed_res['total'] - simple_res['total']} ใบ และน้ำหนักยังอยู่ในเกณฑ์ปลอดภัย!")
elif simple_res['total'] > 0:
    st.info("💡 จำนวนพาเลทที่จัดวางได้ไม่ต่างกันในแง่การใช้งาน สามารถเลือกรูปแบบที่สะดวกต่อการขนถ่าย (Forklift Operation) ได้เลยครับ")
