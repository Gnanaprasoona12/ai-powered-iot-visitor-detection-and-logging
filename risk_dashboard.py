import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Visitor Dashboard", layout="wide")

st.title("🚪 Smart Visitor Access Dashboard")

# =========================
# LOAD DATA
# =========================
def load_data():
    conn = sqlite3.connect("visitor_logs.db")
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    conn.close()
    return df

def load_visitors():
    conn = sqlite3.connect("visitor_logs.db")
    df = pd.read_sql_query("SELECT * FROM visitors", conn)
    conn.close()
    return df

df = load_data()
visitors_df = load_visitors()

# =========================
# FILTERS
# =========================
st.sidebar.header("🔍 Filters")

person_filter = st.sidebar.selectbox(
    "Person Type",
    ["All", "Resident", "Visitor"]
)

status_filter = st.sidebar.selectbox(
    "Access Status",
    ["All", "GRANTED", "DENIED"]
)

# Apply filters
filtered_df = df.copy()

if person_filter != "All":
    filtered_df = filtered_df[filtered_df["person_type"] == person_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"].str.contains(status_filter)]

# =========================
# METRICS
# =========================
st.subheader("📊 System Overview")

col1, col2, col3 = st.columns(3)

total = len(df)
granted = len(df[df["status"].str.contains("GRANTED")])
denied = len(df[df["status"].str.contains("DENIED")])

col1.metric("Total Visits", total)
col2.metric("Access Granted", granted)
col3.metric("Access Denied", denied)

# =========================
# LOG TABLE
# =========================
st.subheader("📋 Access Logs")

st.dataframe(filtered_df, width="stretch")

# =========================
# VISITOR HISTORY
# =========================
st.subheader("🧠 Visitor Behavior Tracking")

if not visitors_df.empty:
    st.dataframe(visitors_df, width="stretch")
else:
    st.write("No visitor history yet")

# =========================
# IMAGE DISPLAY
# =========================
st.subheader("🖼️ Visitor Images")

for _, row in filtered_df.iterrows():
    col1, col2 = st.columns([1, 3])

    with col1:
        if os.path.exists(row["image_path"]):
            img = Image.open(row["image_path"])
            st.image(img, width=150)
        else:
            st.write("No Image")

    with col2:
        st.write(f"🕒 **Time:** {row['timestamp']}")
        st.write(f"👤 **Type:** {row['person_type']}")
        st.write(f"📍 **Room:** {row['room']}")

        status_text = row["status"]

        if "risk_score" in row and pd.notna(row["risk_score"]):
            risk = int(row["risk_score"])
            if risk > 70:
                st.error(f"🚨 HIGH RISK: {risk}")
            elif risk > 30:
                st.warning(f"⚠️ MEDIUM RISK: {risk}")
            else:
                st.success(f"✅ LOW RISK: {risk}")

        st.write(f"🚪 **Status:** {status_text}")
        st.markdown("---")

# =========================
# SIDEBAR SUMMARY
# =========================
st.sidebar.markdown("### 📊 Summary")

st.sidebar.write(f"Total Entries: {total}")
st.sidebar.write(f"Granted: {granted}")
st.sidebar.write(f"Denied: {denied}")