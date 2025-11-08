import streamlit as st
import requests
import time
import json

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="💹 Financial Ratio Tutor", layout="wide")

st.markdown("""
<div class="app-title">💼 Financial Ratio Explanation Tutor</div>
<p style="text-align:center; opacity:0.8;">
Upload your Balance Sheet & Profit & Loss CSV files to compute and interpret financial ratios.
</p>
""", unsafe_allow_html=True)

bs = st.file_uploader("📘 Upload balance_sheet.csv", type=["csv"])
pnl = st.file_uploader("📗 Upload pnl.csv", type=["csv"])
context = st.text_area("📝 Optional context or notes", placeholder="e.g., Manufacturing company FY2024")

analyze_clicked = st.button("🚀 Analyze", use_container_width=True)

if analyze_clicked:
    if not (bs and pnl):
        st.warning("⚠️ Please upload both CSV files.")
        st.stop()

    with st.spinner("⏳ Uploading & computing ratios..."):
        files = {
            "balance_sheet": (bs.name, bs, "text/csv"),
            "pnl": (pnl.name, pnl, "text/csv")
        }
        data = {"context": context or ""}
        try:
            resp = requests.post("http://127.0.0.1:8001/upload", files=files, data=data, timeout=60)
        except Exception as e:
            st.error(f"❌ Backend not reachable: {e}")
            st.stop()
        payload = resp.json()
        st.success(payload.get("status", "✅ Ratios computed successfully!"))
        ratios = payload.get("ratios", {})
        st.subheader("📊 Computed Ratios")
        st.table([[k, v] for k, v in ratios.items()])

    st.info("🧠 Generating explanations…")
    explanations = None

    for _ in range(30):
        time.sleep(2)
        try:
            exp_resp = requests.get("http://127.0.0.1:8001/explanations", timeout=10)
            exp_data = exp_resp.json()
        except:
            continue
        if "explanations" in exp_data:
            explanations = exp_data["explanations"]
            break

    if not explanations:
        st.warning("⚠️ Explanations took too long. Try again.")
        st.stop()

    st.success("✅ Explanations ready!")
    ratio_text = explanations.get("ratio_text", "")
    ratio_blocks = [b.strip() for b in ratio_text.split("---") if b.strip()]

    # ==== Duplicate-safe grid for four ratios only ====
    main_ratios = ["Current Ratio", "Quick Ratio", "Cash Ratio", "Debt-to-Equity"]
    filtered_blocks = []
    for rname in main_ratios:
        block = next((b for b in ratio_blocks if rname in b and b not in filtered_blocks), None)
        if block:
            filtered_blocks.append(block)

    cards_html = "".join(
        f"<div class='explain-card'><pre style='white-space:pre-line'>{block}</pre></div>"
        for block in filtered_blocks
    )
    full_html = f"<div class='explain-grid'>{cards_html}</div>"
    st.markdown(full_html, unsafe_allow_html=True)
    # =====================================

    summary_text = explanations.get("summary_text", "")
    st.markdown(f"<div class='summary-block'><b>📝 Summary</b><br>{summary_text}</div>", unsafe_allow_html=True)

st.subheader("💬 Ask a Follow-up Question")
question = st.text_input("Your question", placeholder="e.g., Why is my DSCR low?")

if st.button("Ask"):
    if question.strip():
        with st.spinner("Thinking..."):
            resp = requests.post("http://127.0.0.1:8001/ask", data={"question": question}, timeout=60)
            st.markdown("### 🧾 Answer")
            st.write(resp.json().get("answer", "No answer received."))
    else:
        st.warning("Please type your question.")
