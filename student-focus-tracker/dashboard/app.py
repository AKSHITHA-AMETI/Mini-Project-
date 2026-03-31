import streamlit as st
import pandas as pd
import requests
import os

try:
    API_BASE = st.secrets["api_base"]
except:
    API_BASE = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000")

@st.cache_data(ttl=8)
def fetch_history(limit=240):
    try:
        resp = requests.get(f"{API_BASE}/history", params={"limit": limit}, timeout=3)
        if resp.ok:
            data = resp.json().get("history", [])
            df = pd.DataFrame(data)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df.sort_values("timestamp", inplace=True)
            return df
    except Exception as e:
        st.error(f"Error fetching history: {e}")
    return pd.DataFrame()


@st.cache_data(ttl=10)
def fetch_stats():
    try:
        resp = requests.get(f"{API_BASE}/stats", timeout=3)
        if resp.ok:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
    return {}


def main():
    st.set_page_config(page_title="Student Focus Dashboard", layout="wide")
    st.title("Student Focus Tracker Dashboard")

    st.sidebar.header("Settings")
    history_limit = st.sidebar.number_input("History points", min_value=20, max_value=1000, value=240, step=20)

    st.sidebar.markdown("---")
    st.sidebar.write("API Base URL")
    st.sidebar.code(API_BASE)

    stats = fetch_stats()
    history = fetch_history(history_limit)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", stats.get("count", 0))
    col2.metric("Average Focus", f"{stats.get('average_score', 0.0):.1f}%")
    if stats.get("latest"):
        col3.metric("Latest Score", f"{stats['latest'].get('focus_score', 0.0):.1f}%")
    else:
        col3.metric("Latest Score", "N/A")

    if history.empty:
        st.warning("No history data available yet. Start backend + main app to begin collecting data.")
    else:
        st.subheader("Focus Score Time Series")
        st.line_chart(history.set_index("timestamp")["focus_score"])
        st.subheader("Raw Table")
        st.dataframe(history[["timestamp", "gaze", "head_direction", "yawning", "laughing", "focus_score"]].sort_values("timestamp", ascending=False))
    if st.button("Refresh now"):
        st.cache_data.clear()
        st.rerun()
    st.info("Dashboard auto-refreshes every 10 seconds")
if __name__ == "__main__":
    main()
