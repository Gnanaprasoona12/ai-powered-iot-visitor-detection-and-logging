import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import os

# Page settings
st.set_page_config(page_title="Visitor Dashboard", layout="wide")

st.title("🚪 Smart Visitor Access Dashboard")

# Load data
def load_data():
    conn = sqlite3.connect("visitor_logs.db")
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    conn.close()
    return df

df = load_data()

# Filters
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
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

# Show table
st.subheader("📋 Access Logs")
st.dataframe(filtered_df, width="stretch")

# Show images
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
        st.write(f"🚪 **Status:** {row['status']}")
        st.markdown("---")

# Stats
st.sidebar.markdown("### 📊 Summary")

total = len(df)
granted = len(df[df["status"] == "GRANTED"])
denied = len(df[df["status"] == "DENIED"])

st.sidebar.write(f"Total Entries: {total}")
st.sidebar.write(f"Granted: {granted}")
st.sidebar.write(f"Denied: {denied}")