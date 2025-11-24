import streamlit as st
import requests
import pandas as pd

# ----------- PAGE CONFIG -----------
st.set_page_config(
    page_title="Gmail Spam Detector",
    page_icon="📧",
    layout="wide",
)

st.markdown("""
# 📧 Gmail Spam Detection Dashboard  
Scan, view, and delete spam emails safely using your ML model.
""")

# ----------- SESSION STATE INIT -----------
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None

if "selected_id" not in st.session_state:
    st.session_state.selected_id = None


# ----------- SIDEBAR -----------
with st.sidebar:
    st.header("🔐 Gmail Login")
    email_user = st.text_input("Enter Gmail Address", placeholder="your@gmail.com")
    app_password = st.text_input("Enter App Password (16 chars)", type="password", placeholder="xxxx xxxx xxxx xxxx")

    limit = st.slider("Number of recent emails to scan", 5, 200, 20)
    show_spam_only = st.checkbox("Show only SPAM emails", value=True)
    allow_delete = st.checkbox("Enable Delete Option", value=False)

    backend_url = "http://localhost:5000/scan"
    delete_url = "http://localhost:5000/delete"

    st.info("Use Gmail App Password — NOT your normal Gmail password.")


# ----------- SCAN BUTTON -----------
if st.button("🚀 Scan Gmail"):
    if not email_user or not app_password:
        st.error("Please enter Gmail and App Password.")
    else:
        with st.spinner("Scanning your Gmail..."):
            response = requests.post(
                backend_url,
                json={
                    "email": email_user,
                    "app_password": app_password,
                    "limit": limit
                }
            )

        if response.status_code != 200:
            st.error("❌ Backend error occurred")
            st.code(response.text)
        else:
            st.session_state.scan_results = response.json()
            st.success("✔ Scan Completed Successfully!")
            st.session_state.selected_id = None  # Reset selection


# ----------- SHOW RESULTS -----------
if st.session_state.scan_results:

    df = pd.DataFrame(st.session_state.scan_results)

    # Filter only SPAM if checkbox enabled
    if show_spam_only:
        df = df[df["label"] == "SPAM"]

    if df.empty:
        st.warning("No emails found to display.")
    else:
        st.markdown("## 📬 Email Summary")
        st.dataframe(
            df[["id", "from", "subject", "date"]],
            use_container_width=True
        )

        # ----------- EMAIL PREVIEW SECTION -----------
        st.markdown("## 🔎 Email Preview")

        id_list = df["id"].tolist()

        # Keep last selected ID if possible
        default_index = 0
        if st.session_state.selected_id in id_list:
            default_index = id_list.index(st.session_state.selected_id)

        selected_id = st.selectbox(
            "Select an Email ID to preview its cleaned text",
            id_list,
            index=default_index
        )

        # Update stored selected ID
        st.session_state.selected_id = selected_id

        # Extract selected row
        selected_row = df[df["id"] == selected_id].iloc[0]

        # Display details
        st.write("**From:**", selected_row["from"])
        st.write("**Subject:**", selected_row["subject"])
        st.write("**Date:**", selected_row["date"])
        st.write("**Prediction:**", "🟥 SPAM" if selected_row["label"] == "SPAM" else "🟩 HAM")

        st.markdown("### Cleaned Email Text")
        st.code(selected_row["clean_text"])

        # ----------- DELETE OPTION -----------
        if allow_delete and selected_row["label"] == "SPAM":
            st.warning("⚠ Deleting will permanently remove this email from Gmail")

            if st.button("🗑 DELETE THIS EMAIL"):
                delete_res = requests.post(
                    delete_url,
                    json={
                        "email": email_user,
                        "app_password": app_password,
                        "mail_id": selected_id
                    }
                )

                if delete_res.status_code == 200:
                    # Remove deleted email locally
                    st.session_state.scan_results = [
                        email for email in st.session_state.scan_results
                        if email["id"] != selected_id
                    ]
                    st.session_state.selected_id = None

                    st.success("🗑 Email Deleted Successfully!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Failed to delete email")


st.markdown("---")
st.caption("Made by Nishant • Gmail Spam Detection System 🚀")
