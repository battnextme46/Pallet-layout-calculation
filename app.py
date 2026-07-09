
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

st.set_page_config(
    page_title="Pallet Optimizer",
    layout="wide"
)

st.title("📦 Pallet Container Layout Optimizer")
st.write("เครื่องมือคำนวณการจัดวางพาเลทในตู้คอนเทนเนอร์แบบ Mixed Orientation")

# =========================
# SIDEBAR
# =========================

st.sidebar.header("1. ข้อมูลพาเลท (cm)")

p_w = st.sidebar.number_input(
    "ความกว้างพาเลท (Width)",
    min_value=1.0,
    value=80.0
)

p_l = st.sidebar.number_input(
    "ความยาวพาเลท (Length)",
    min_value=1.0,
    value=120.0
)

st.sidebar.header("2. น้ำหนักพาเลท")

weight_per_pallet = st.sidebar.number_input(
    "น้ำหนักต่อพาเลท (kg)",
    min_value=0.0,
    value=500.0,
    step=10.0
)

st.sidebar.header("3. ข้อมูลตู้คอนเทนเนอร์")

c_type = st.sidebar.selectbox(
    "ประเภทตู้",
    ["20ft", "40ft"]
)

c_w_raw = 235.0
c_l_raw = 590.0 if c_type == "20ft" else 1203.0

payload_limit = 28200.0 if c_type == "20ft" else 26700.0

st.sidebar.header("4. ระยะเผื่อความปลอดภัย (Clearance)")

c_w_gap = st.sidebar.slider(
    "ระยะเผื่อด้านกว้าง (Total W)",
    0.0,
    20.0,
    5.0
)

c_l_gap = st.sidebar.slider(
    "ระยะเผื่อด้านยาว (Total L)",
    0.0,
    30.0,
    10.0
)

# =========================
# SOLVER
# =========================

def solve_layout(pw, pl, cw_raw, cl_raw, cw_clear, cl_clear):

    cw = cw_raw - cw_clear
    cl = cl_raw - cl_clear

    o1 = (cw // pw) * (cl // pl)
    o2 = (cw // pl) * (cl // pw)

    if o1 >= o2:
        simple = {
            "n_rows": int(cw // pw),
            "n_type_w": pw,
            "n_type_l": pl,
            "n_per_row": int(cl // pl),
            "m_rows": 0,
            "total": int(o1)
        }
    else:
        simple = {
            "n_rows": int(cw // pl),
            "n_type_w": pl,
            "n_type_l": pw,
            "n_per_row": int(cl // pw),
            "m_rows": 0,
            "total": int(o2)
        }

    best_mixed = {"total": 0}

    for n in range(int(cw // pw) + 1):

        m = int((cw - (n * pw)) // pl)

        total = (
            n * (cl // pl)
            + m * (cl // pw)
        )

        if total > best_mixed["total"]:

            best_mixed = {
                "n_rows": n,
                "n_type_w": pw,
                "n_type_l": pl,
                "n_per_row": int(cl // pl),
                "m_rows": m,
                "m_type_w": pl,
                "m_type_l": pw,
                "m_per_row": int(cl // pw),
                "total": int(total)
            }

    return simple, best_mixed


simple_res, mixed_res = solve_layout(
    p_w,
    p_l,
    c_w_raw,
    c_l_raw,
    c_w_gap,
    c_l_gap
)

# =========================
# CALCULATIONS
# =========================

usable_area = (
    (c_w_raw - c_w_gap)
    * (c_l_raw - c_l_gap)
)

simple_area = simple_res["total"] * p_w * p_l
mixed_area = mixed_res["total"] * p_w * p_l

simple_util = (
    simple_area / usable_area * 100
    if usable_area > 0 else 0
)

mixed_util = (
    mixed_area / usable_area * 100
    if usable_area > 0 else 0
)

simple_weight = simple_res["total"] * weight_per_pallet
mixed_weight = mixed_res["total"] * weight_per_pallet

# =========================
# DRAWING
# =========================

def draw_plot(res, title):

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.add_patch(
        patches.Rectangle(
            (0, 0),
            c_l_raw,
            c_w_raw,
            linewidth=3,
            edgecolor="black",
            facecolor="white"
        )
    )

    usable_l = c_l_raw - c_l_gap
    usable_w = c_w_raw - c_w_gap

    ax.add_patch(
        patches.Rectangle(
            (c_l_gap / 2, c_w_gap / 2),
            usable_l,
            usable_w,
            linewidth=1,
            edgecolor="gray",
            facecolor="#f8fafc",
            linestyle="--"
        )
    )

    used_w = (
        res["n_rows"] * res["n_type_w"]
        + res.get("m_rows", 0) * res.get("m_type_w", 0)
    )

    curr_y = (c_w_raw - used_w) / 2

    def draw_group(rows, per_row, pallet_w, pallet_l, start_y):

        y = start_y

        for _ in range(rows):

            off_x = (
                c_l_raw - (per_row * pallet_l)
            ) / 2

            for j in range(per_row):

                ax.add_patch(
                    patches.Rectangle(
                        (off_x + j * pallet_l, y),
                        pallet_l,
                        pallet_w,
                        edgecolor="#0369a1",
                        facecolor="#bae6fd"
                    )
                )

            y += pallet_w

        return y

    next_y = draw_group(
        res["n_rows"],
        res["n_per_row"],
        res["n_type_w"],
        res["n_type_l"],
        curr_y
    )

    if res.get("m_rows", 0) > 0:

        draw_group(
            res["m_rows"],
            res["m_per_row"],
            res["m_type_w"],
            res["m_type_l"],
            next_y
        )

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{title}: {res['total']} UNITS")

    return fig

# =========================
# DISPLAY
# =========================

col1, col2 = st.columns(2)

with col1:

    st.subheader("OPTION 1 : SIMPLE GRID")

    st.metric(
        "Pallet Qty",
        simple_res["total"]
    )

    fig1 = draw_plot(simple_res, "OPTION 1")
    st.pyplot(fig1)
    plt.close(fig1)

    st.write(f"**Total Weight :** {simple_weight:,.0f} kg")
    st.write(f"**Utilization :** {simple_util:.1f}%")

    if simple_weight > payload_limit:
        st.error(
            f"⚠️ Payload Exceeded ({payload_limit:,.0f} kg)"
        )
    else:
        st.success(
            f"✅ Payload OK ({payload_limit:,.0f} kg)"
        )

with col2:

    st.subheader("OPTION 2 : MIXED ORIENTATION")

    st.metric(
        "Pallet Qty",
        mixed_res["total"]
    )

    fig2 = draw_plot(mixed_res, "OPTION 2")
    st.pyplot(fig2)
    plt.close(fig2)

    st.write(f"**Total Weight :** {mixed_weight:,.0f} kg")
    st.write(f"**Utilization :** {mixed_util:.1f}%")

    if mixed_weight > payload_limit:
        st.error(
            f"⚠️ Payload Exceeded ({payload_limit:,.0f} kg)"
        )
    else:
        st.success(
            f"✅ Payload OK ({payload_limit:,.0f} kg)"
        )

# =========================
# RECOMMENDATION
# =========================

st.divider()

if mixed_res["total"] > simple_res["total"]:

    st.success(
        f"🔥 Recommend OPTION 2 : +{mixed_res['total'] - simple_res['total']} pallets"
    )

else:

    st.info(
        "💡 Both options provide the same quantity."
    )
