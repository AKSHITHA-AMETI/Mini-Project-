import streamlit as st
import pandas as pd
import requests
import os
import webbrowser

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


@st.cache_data(ttl=5)
def fetch_stats():
    try:
        resp = requests.get(f"{API_BASE}/stats", timeout=3)
        if resp.ok:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
    return {}

@st.cache_data(ttl=10)
def fetch_meeting_url():
    try:
        resp = requests.get(f"{API_BASE}/meeting", timeout=3)
        if resp.ok:
            return resp.json().get("url", "")
    except Exception as e:
        st.error(f"Error fetching meeting URL: {e}")
    return ""

def set_meeting_url(url):
    try:
        resp = requests.post(f"{API_BASE}/meeting", json={"url": url}, timeout=3)
        return resp.ok
    except Exception as e:
        st.error(f"Error setting meeting URL: {e}")
        return False


def login_page():
    st.title("Student Focus Tracker")
    st.subheader("Login")

    role = st.selectbox("Select your role:", ["Student", "Teacher"])

    if st.button("Login"):
        st.session_state["logged_in"] = True
        st.session_state["role"] = role
        st.rerun()

    st.markdown("---")
    st.write("**Student**: Join the class through the URL provided by your teacher")
    st.write("**Teacher**: Set the meeting URL and monitor student attention data")


def student_page():
    st.title("Student Dashboard")
    st.subheader("Join Class Meeting")

    meeting_url = fetch_meeting_url()

    if meeting_url:
        st.write(f"**Class Meeting URL:** {meeting_url}")
        st.info("You must join through this official class URL provided by your teacher.")

        if st.button("Join Meeting & Start Tracking"):
            st.success(f"Opening meeting: {meeting_url}")
            st.info("Focus tracking will start automatically. Keep this window open.")
            webbrowser.open(meeting_url)
            st.session_state["tracking"] = True

        if st.session_state.get("tracking", False):
            st.markdown("---")
            st.subheader("Focus Tracking Active")
            st.write(f"Meeting: {meeting_url}")

            # Show current stats
            stats = fetch_stats()
            if stats.get("latest"):
                col1, col2 = st.columns(2)
                col1.metric("Current Focus Score", f"{stats['latest'].get('focus_score', 0.0):.1f}%")
                col2.metric("Gaze Direction", stats['latest'].get("gaze", "Unknown"))

            if st.button("Stop Tracking"):
                st.session_state["tracking"] = False
                st.success("Tracking stopped")
                st.rerun()
    else:
        st.warning("No meeting URL set by teacher yet. Please wait for the teacher to provide the class URL.")
        st.info("Refresh this page once the teacher has set the meeting URL.")


def teacher_page():
    st.title("Teacher Dashboard")
    st.subheader("Student Focus Monitoring")

    st.sidebar.header("Settings")
    history_limit = st.sidebar.number_input("History points", min_value=20, max_value=1000, value=240, step=20)

    # Meeting URL setup
    st.sidebar.markdown("---")
    st.sidebar.subheader("Meeting Setup")
    current_url = fetch_meeting_url()
    meeting_url = st.sidebar.text_input("Set Meeting URL for Students:", value=current_url, placeholder="https://meet.google.com/abc-defg-hij")
    if st.sidebar.button("Set Meeting URL"):
        if set_meeting_url(meeting_url):
            st.sidebar.success("Meeting URL updated for students")
            st.cache_data.clear()  # Clear cache to refresh
        else:
            st.sidebar.error("Failed to update URL")

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
        st.warning("No history data available yet. Students need to start tracking.")
    else:
        st.subheader("Focus Score Time Series")
        st.line_chart(history.set_index("timestamp")["focus_score"])
        st.subheader("Raw Table")
        st.dataframe(history[["timestamp", "head_direction", "focus_score"]].sort_values("timestamp", ascending=False))
    if st.button("Refresh now"):
        st.cache_data.clear()
        st.rerun()
    st.info("Dashboard auto-refreshes every 10 seconds")


def main():
    if not st.session_state.get("logged_in", False):
        login_page()
    else:
        role = st.session_state.get("role", "Student")

        if role == "Student":
            student_page()
        else:
            teacher_page()

        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()


if __name__ == "__main__":
    main()
