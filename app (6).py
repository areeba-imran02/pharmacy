"""
Smart Pharmacy Stock Assistant - Hackathon Project
Auto stock tracking, AI low-stock prediction, expiry alerts, AI chat query,
photo-based stock entry (Groq Vision), light/dark theme.
"""

import streamlit as st
import json
import os
import base64
from datetime import datetime, date
from groq import Groq

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Pharmacy Assistant",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "medicines.json")

# ---------------- API KEY ----------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
if not GROQ_API_KEY:
    GROQ_API_KEY = st.sidebar.text_input("🔑 Groq API Key", type="password",
                                          help="console.groq.com/keys se free milti hai")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ---------------- DATA HELPERS ----------------
def load_data():
    if "medicines" not in st.session_state:
        with open(DATA_FILE, "r") as f:
            st.session_state.medicines = json.load(f)
    return st.session_state.medicines

def save_runtime():
    pass  # in-memory only for demo; swap with DB/file write for production

def next_id():
    meds = load_data()
    return max([m["id"] for m in meds], default=0) + 1

def days_until(expiry_str):
    exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
    return (exp - date.today()).days

def days_to_stockout(med):
    if med["avg_daily_sales"] <= 0:
        return None
    return int(med["quantity"] / med["avg_daily_sales"])

# ---------------- THEME ----------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def theme_css(theme):
    if theme == "dark":
        return """
        <style>
        .stApp { background-color: #0e1117; color: #e6e6e6; }
        .metric-card {
            background: linear-gradient(145deg, #1a1f2b, #12151d);
            border: 1px solid #2a2f3a;
            border-radius: 14px; padding: 18px 20px; margin-bottom: 10px;
        }
        .metric-title { color: #9aa4b2; font-size: 13px; font-weight: 500; letter-spacing: .3px; }
        .metric-value { font-size: 30px; font-weight: 700; margin-top: 4px; }
        .pill-red { color: #ff6b6b; }
        .pill-orange { color: #ffb454; }
        .pill-green { color: #5fe0a0; }
        .med-row {
            background: #161a23; border-radius: 10px; padding: 12px 16px;
            margin-bottom: 8px; border-left: 4px solid #2a2f3a;
        }
        .med-row.low { border-left: 4px solid #ff6b6b; }
        .med-row.warn { border-left: 4px solid #ffb454; }
        .med-row.ok { border-left: 4px solid #5fe0a0; }
        .app-header { font-size: 34px; font-weight: 800; margin-bottom: 0px; }
        .app-sub { color: #9aa4b2; margin-top: -6px; margin-bottom: 20px; }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color: #f7f8fa; color: #1a1a1a; }
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f0f1f5);
            border: 1px solid #e2e5eb;
            border-radius: 14px; padding: 18px 20px; margin-bottom: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }
        .metric-title { color: #6b7280; font-size: 13px; font-weight: 500; letter-spacing: .3px; }
        .metric-value { font-size: 30px; font-weight: 700; margin-top: 4px; color: #111827; }
        .pill-red { color: #dc2626; }
        .pill-orange { color: #d97706; }
        .pill-green { color: #16a34a; }
        .med-row {
            background: #ffffff; border-radius: 10px; padding: 12px 16px;
            margin-bottom: 8px; border-left: 4px solid #e2e5eb;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .med-row.low { border-left: 4px solid #dc2626; }
        .med-row.warn { border-left: 4px solid #d97706; }
        .med-row.ok { border-left: 4px solid #16a34a; }
        .app-header { font-size: 34px; font-weight: 800; margin-bottom: 0px; color: #111827; }
        .app-sub { color: #6b7280; margin-top: -6px; margin-bottom: 20px; }
        </style>
        """

st.markdown(theme_css(st.session_state.theme), unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 💊 PharmaSmart")
theme_choice = st.sidebar.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
st.session_state.theme = "dark" if theme_choice else "light"

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "➕ Add / Sell Stock", "📷 Scan Medicine Photo", "⏰ Expiry Tracker", "💬 Ask AI"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Groq API (Llama 3.3 + Vision)")

# ---------------- HEADER ----------------
st.markdown('<div class="app-header">Smart Pharmacy Stock Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="app-sub">Auto stock tracking • AI predictions • Expiry alerts • Natural language queries</div>', unsafe_allow_html=True)

meds = load_data()

# ================= DASHBOARD =================
if page == "📊 Dashboard":
    low_stock = [m for m in meds if m["quantity"] <= m["threshold"]]
    expiring_soon = [m for m in meds if days_until(m["expiry_date"]) <= 90]
    total_value = sum(m["quantity"] * m["price"] for m in meds)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">TOTAL MEDICINES</div>'
                     f'<div class="metric-value">{len(meds)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">LOW STOCK ALERTS</div>'
                     f'<div class="metric-value pill-red">{len(low_stock)}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">EXPIRING SOON (90d)</div>'
                     f'<div class="metric-value pill-orange">{len(expiring_soon)}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">INVENTORY VALUE</div>'
                     f'<div class="metric-value pill-green">Rs. {total_value:,}</div></div>', unsafe_allow_html=True)

    st.markdown("### 🚨 Low Stock — Needs Reorder")
    if low_stock:
        for m in sorted(low_stock, key=lambda x: x["quantity"]):
            dts = days_to_stockout(m)
            eta_text = f"~{dts} din mein khatam" if dts is not None else "N/A"
            st.markdown(
                f'<div class="med-row low"><b>{m["name"]}</b> — Stock: {m["quantity"]} '
                f'(threshold {m["threshold"]}) &nbsp;|&nbsp; ⏳ {eta_text} '
                f'&nbsp;|&nbsp; Batch: {m["batch"]}</div>', unsafe_allow_html=True
            )
    else:
        st.success("Sab stock levels theek hain ✅")

    st.markdown("### 📋 Full Inventory")
    for m in sorted(meds, key=lambda x: x["name"]):
        status = "low" if m["quantity"] <= m["threshold"] else "ok"
        st.markdown(
            f'<div class="med-row {status}"><b>{m["name"]}</b> ({m["batch"]}) — '
            f'Qty: {m["quantity"]} &nbsp;|&nbsp; Price: Rs. {m["price"]} &nbsp;|&nbsp; '
            f'Expiry: {m["expiry_date"]}</div>', unsafe_allow_html=True
        )

# ================= ADD / SELL STOCK =================
elif page == "➕ Add / Sell Stock":
    tab1, tab2 = st.tabs(["➕ Add New / Restock", "🧾 Record a Sale"])

    with tab1:
        st.subheader("Add New Medicine or Restock Existing")
        existing_names = [m["name"] for m in meds]
        mode = st.radio("Type", ["Restock existing", "Add brand new medicine"], horizontal=True)

        if mode == "Restock existing":
            sel = st.selectbox("Select medicine", existing_names)
            add_qty = st.number_input("Quantity to add", min_value=1, value=10)
            if st.button("✅ Restock"):
                for m in meds:
                    if m["name"] == sel:
                        m["quantity"] += add_qty
                st.success(f"{sel} restocked with {add_qty} units.")
                st.rerun()
        else:
            with st.form("new_med"):
                name = st.text_input("Medicine Name")
                batch = st.text_input("Batch Number")
                qty = st.number_input("Initial Quantity", min_value=0, value=20)
                threshold = st.number_input("Low-stock Threshold", min_value=1, value=15)
                price = st.number_input("Price per unit (Rs.)", min_value=0, value=50)
                expiry = st.date_input("Expiry Date")
                avg_sales = st.number_input("Estimated avg daily sales", min_value=0, value=3)
                submitted = st.form_submit_button("➕ Add Medicine")
                if submitted and name:
                    meds.append({
                        "id": next_id(), "name": name, "batch": batch, "quantity": qty,
                        "threshold": threshold, "expiry_date": str(expiry), "price": price,
                        "avg_daily_sales": avg_sales
                    })
                    st.success(f"{name} added to inventory.")
                    st.rerun()

    with tab2:
        st.subheader("Record a Sale (auto stock deduction)")
        sel = st.selectbox("Medicine sold", [m["name"] for m in meds], key="sell_select")
        qty_sold = st.number_input("Quantity sold", min_value=1, value=1)
        if st.button("🧾 Confirm Sale"):
            for m in meds:
                if m["name"] == sel:
                    if m["quantity"] >= qty_sold:
                        m["quantity"] -= qty_sold
                        st.success(f"Sold {qty_sold} x {sel}. Remaining: {m['quantity']}")
                        if m["quantity"] <= m["threshold"]:
                            st.warning(f"⚠️ {sel} is now below threshold — reorder soon!")
                    else:
                        st.error("Not enough stock available.")
            st.rerun()

# ================= PHOTO SCAN =================
elif page == "📷 Scan Medicine Photo":
    st.subheader("Upload a photo of the medicine box/strip")
    st.caption("AI packaging se naam, batch number, aur expiry date read karne ki koshish karega (verify zaroor karein).")
    img_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if img_file and client:
        st.image(img_file, width=300)
        if st.button("🔍 Extract Details with AI"):
            with st.spinner("Reading packaging..."):
                b64_img = base64.b64encode(img_file.read()).decode("utf-8")
                try:
                    response = client.chat.completions.create(
                        model="llama-3.2-90b-vision-preview",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract from this medicine packaging: medicine name, batch number, expiry date. Reply in short plain text, one field per line."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                            ]
                        }],
                        max_tokens=300
                    )
                    st.info(response.choices[0].message.content)
                    st.caption("Details ko upar 'Add / Sell Stock' page mein manually confirm kar ke add karein.")
                except Exception as e:
                    st.error(f"Vision model error: {e}")
    elif img_file and not client:
        st.warning("Pehle Groq API key sidebar mein enter karein.")

# ================= EXPIRY TRACKER =================
elif page == "⏰ Expiry Tracker":
    st.subheader("Medicines by Expiry Date")
    sorted_meds = sorted(meds, key=lambda x: x["expiry_date"])
    for m in sorted_meds:
        d = days_until(m["expiry_date"])
        if d <= 30:
            cls, tag = "low", f"🔴 {d} din baqi — URGENT, discount/clear karein"
        elif d <= 90:
            cls, tag = "warn", f"🟠 {d} din baqi — jald sell karein"
        else:
            cls, tag = "ok", f"🟢 {d} din baqi — safe"
        st.markdown(
            f'<div class="med-row {cls}"><b>{m["name"]}</b> ({m["batch"]}) — '
            f'Expiry: {m["expiry_date"]} &nbsp;|&nbsp; {tag}</div>', unsafe_allow_html=True
        )

# ================= AI CHAT =================
elif page == "💬 Ask AI":
    st.subheader("Pooch lein apne stock ke baray mein — kuch bhi")
    st.caption('Misal: "Kitni Panadol bachi hai?" ya "Is hafte konsi medicines khatam hone wali hain?"')

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    q = st.chat_input("Apna sawal likhein...")
    if q and client:
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)

        stock_context = "\n".join([
            f'- {m["name"]} | Batch {m["batch"]} | Qty: {m["quantity"]} | Threshold: {m["threshold"]} | '
            f'Expiry: {m["expiry_date"]} | Price: Rs.{m["price"]} | Avg daily sales: {m["avg_daily_sales"]}'
            for m in meds
        ])

        system_prompt = f"""You are a pharmacy stock assistant. Answer ONLY using the inventory data below.
If the user's question can't be answered from this data, say so honestly.
Respond in the same language style the user used (Roman Urdu, Urdu, or English). Be concise and specific with numbers.

INVENTORY:
{stock_context}
"""
        with st.chat_message("assistant"):
            with st.spinner("Checking stock..."):
                try:
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": system_prompt}] + st.session_state.chat_history,
                        temperature=0.3,
                        max_tokens=500
                    )
                    reply = resp.choices[0].message.content
                except Exception as e:
                    reply = f"⚠️ Error: {e}"
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
    elif q and not client:
        st.warning("Pehle Groq API key sidebar mein enter karein.")
