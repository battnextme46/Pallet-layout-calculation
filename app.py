import streamlit as st

# ตั้งค่าหน้าเว็บให้แสดงผลแบบกว้างและสวยงาม
st.set_page_config(
    page_title="Pallet Optimizer", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 Pallet Container Layout Optimizer")
st.write("เครื่องมือคำนวณการจัดวางพาเลทในตู้คอนเทนเนอร์แบบ Mixed Orientation")

# --- SIDEBAR INPUTS (แถบเมนูด้านซ้าย) ---
st.sidebar.header("1. ข้อมูลพาเลท (cm)")
p_w = st.sidebar.number_input("ความกว้างพาเลท (Width)", value=80.0, step=5.0)
p_l = st.sidebar.number_input("ความยาวพาเลท (Length)", value=120.0, step=5.0)

st.sidebar.header("2. ข้อมูลตู้คอนเทนเนอร์")
c_type = st.sidebar.selectbox("ประเภทตู้", ["20ft", "40ft"])
c_w_raw = 235.0
c_l_raw = 590.0 if c_type == "20ft" else 1203.0

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

# --- SVG PLOTTING ENGINE (วาดรูปกราฟิกด้วยระบบเวกเตอร์ - ปลอดภัย 100%) ---
def generate_svg_plot(res, title):
    # กำหนดสัดส่วนภาพให้แสดงผลพอดีหน้าจอ
    view_box_w = c_l_raw
    view_box_h = c_w_raw
    
    # เริ่มต้นสร้างเนื้อหา SVG
    svg = f'<svg width="100%" height="auto" viewBox="0 0 {view_box_w} {view_box_h}" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 3px solid #1e293b; border-radius: 8px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">'
    
    # วาดพื้นที่ตู้คอนเทนเนอร์ (เส้นขอบสีดำ)
    svg += f'<rect x="0" y="0" width="{c_l_raw}" height="{c_w_raw}" fill="#f8fafc" stroke="#1e293b" stroke-width="4" />'
    
    # วาดพื้นที่ใช้งานจริงหักระยะเผื่อความปลอดภัย (เส้นประสีเทา)
    usable_l = c_l_raw - c_l_gap
    usable_w = c_w_raw - c_w_gap
    svg += f'<rect x="{c_l_gap/2}" y="{c_w_gap/2}" width="{usable_l}" height="{usable_w}" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6,6" />'
    
    # คอนฟิกการคำนวณตำแหน่งจัดวางพาเลท
    used_w = (res["n_rows"] * res["n_type_w"]) + (res.get("m_rows", 0) * res.get("m_type_w", 0))
    curr_y = (c_w_raw - used_w) / 2
    
    # ฟังก์ชันช่วยวาดบล็อกพาเลทลงในพิกัด SVG
    def draw_pallet_group(n_rows, n_per_row, pw, pl, start_y):
        y = start_y
        rects_html = ""
        for i in range(n_rows):
            off_x = (c_l_raw - (n_per_row * pl)) / 2
            for j in range(n_per_row):
                px = off_x + (j * pl)
                py = y
                # วาดพาเลทสีฟ้าอ่อน ขอบสีน้ำเงินเข้ม
                rects_html += f'<rect x="{px}" y="{py}" width="{pl}" height="{pw}" fill="#bae6fd" stroke="#0284c7" stroke-width="1.5" rx="3" ry="3" />'
                # เขียนข้อความบอกขนาดพาเลทตรงกลางกล่อง
                rects_html += f'<text x="{px + (pl/2)}" y="{py + (pw/2) + 5}" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" fill="#0369a1" text-anchor="middle">{int(pl)}x{int(pw)}</text>'
            y += pw
        return y, rects_html

    # วาดพาเลทแถวหลัก
    next_y, g1_html = draw_pallet_group(res["n_rows"], res["n_per_row"], res["n_type_w"], res["n_type_l"], curr_y)
    svg += g1_html
    
    # วาดพาเลทแถวเสริม (ถ้ามีแบบผสม orientation)
    if res.get("m_rows", 0) > 0:
        _, g2_html = draw_pallet_group(res["m_rows"], res["m_per_row"], res["m_type_w"], res["m_type_l"], next_y)
        svg += g2_html
        
    svg += '</svg>'
    return svg

# --- EXECUTION & DISPLAY (ประมวลผลและแสดงผลลัพธ์) ---
simple_res, mixed_res = solve_layout(p_w, p_l, c_w_raw, c_l_raw, c_w_gap, c_l_gap)

col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 แบบที่ 1: จัดเรียงแบบปกติ (Simple Grid)")
    st.metric(label="จำนวนพาเลทที่จัดวางได้ทั้งหมด", value=f"{simple_res['total']} ใบ")
    # สั่งแสดงภาพ SVG ลงหน้าเว็บโดยตรง
    st.write(generate_svg_plot(simple_res, "Simple Grid"), unsafe_allow_html=True)

with col2:
    st.subheader("⚡ แบบที่ 2: จัดเรียงแบบผสมทิศทาง (Mixed)")
    st.metric(label="จำนวนพาเลทที่จัดวางได้ทั้งหมด", value=f"{mixed_res['total']} ใบ")
    # สั่งแสดงภาพ SVG ลงหน้าเว็บโดยตรง
    st.write(generate_svg_plot(mixed_res, "Mixed Orientation"), unsafe_allow_html=True)

# แจ้งเตือนแนะนำทางเลือกที่ดีที่สุด
if mixed_res["total"] > simple_res["total"]:
    st.success(f"🔥 แนะนำให้เลือกจัดวางแบบที่ 2 (แบบผสม) เพราะสามารถจุพาเลทเพิ่มได้อีก {mixed_res['total'] - simple_res['total']} ใบ!")
elif simple_res["total"] > 0:
    st.info("💡 ทั้งสองแบบจัดวางได้จำนวนเท่ากัน สามารถเลือกใช้แบบที่จัดเรียงได้สะดวกที่สุดได้เลยครับ")
