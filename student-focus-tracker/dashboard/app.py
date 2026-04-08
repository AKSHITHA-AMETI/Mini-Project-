import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# Configuration
try:
    API_BASE = st.secrets["api_base"]
except:
    API_BASE = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000")

# Set page config
st.set_page_config(
    page_title="Student Focus Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

<<<<<<< Updated upstream

@st.cache_data(ttl=5)
def fetch_stats():
    try:
        resp = requests.get(f"{API_BASE}/stats", timeout=3)
        if resp.ok:
            return resp.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
    return {}

@st.cache_data(ttl=5)
def fetch_class_status():
    try:
        resp = requests.get(f"{API_BASE}/class_status", timeout=3)
        if resp.ok:
            return resp.json().get("status", "inactive")
    except Exception as e:
        st.error(f"Error fetching class status: {e}")
    return "inactive"

def set_class_status(status):
    try:
        resp = requests.post(f"{API_BASE}/class_status", json={"status": status}, timeout=3)
        return resp.ok
    except Exception as e:
        st.error(f"Error setting class status: {e}")
        return False

@st.cache_data(ttl=5)
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
=======
# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
>>>>>>> Stashed changes


def login_page():
    """Display login/register page"""
    st.title("Student Focus Tracker")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", key="login_btn"):
            if login_username and login_password:
                try:
                    resp = requests.post(
                        f"{API_BASE}/auth/login",
                        json={"username": login_username, "password": login_password},
                        timeout=3
                    )
                    if resp.ok:
                        data = resp.json()
                        st.session_state.authenticated = True
                        st.session_state.user_id = data["user_id"]
                        st.session_state.username = data["username"]
                        st.session_state.role = data["role"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(resp.json().get("error", "Login failed"))
                except Exception as e:
                    st.error(f"Login error: {e}")
            else:
                st.warning("Please enter username and password")
    
    with col2:
        st.subheader("Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_role = st.radio("Role", ["student", "teacher"], key="reg_role")
        
        if st.button("Register", key="reg_btn"):
            if reg_username and reg_password and reg_role:
                try:
                    resp = requests.post(
                        f"{API_BASE}/auth/register",
                        json={
                            "username": reg_username,
                            "password": reg_password,
                            "email": reg_email,
                            "role": reg_role
                        },
                        timeout=3
                    )
                    if resp.ok:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(resp.json().get("error", "Registration failed"))
                except Exception as e:
                    st.error(f"Registration error: {e}")
            else:
                st.warning("Please fill all required fields")


@st.cache_data(ttl=10)
def fetch_student_classes(user_id):
    """Fetch classes for student"""
    try:
        resp = requests.get(
            f"{API_BASE}/classes",
            params={"user_id": user_id, "role": "student"},
            timeout=3
        )
        if resp.ok:
            return resp.json().get("classes", [])
    except Exception as e:
        st.error(f"Error fetching classes: {e}")
    return []

<<<<<<< Updated upstream
    meeting_url = fetch_meeting_url()
    class_status = fetch_class_status()
=======
>>>>>>> Stashed changes

@st.cache_data(ttl=10)
def fetch_teacher_classes(user_id):
    """Fetch classes for teacher"""
    try:
        resp = requests.get(
            f"{API_BASE}/classes",
            params={"user_id": user_id, "role": "teacher"},
            timeout=3
        )
        if resp.ok:
            return resp.json().get("classes", [])
    except Exception as e:
        st.error(f"Error fetching classes: {e}")
    return []

<<<<<<< Updated upstream
        if class_status != "active":
            st.warning("Class is not active. Tracking will start once the teacher starts the class.")
            st.button("Join Meeting & Start Tracking", disabled=True)
            st.stop()

        if st.button("Join Meeting & Start Tracking"):
            st.success(f"Opening meeting: {meeting_url}")
            st.info("Focus tracking will start automatically. Keep this window open.")
            webbrowser.open(meeting_url)
            st.session_state["tracking"] = True
=======
>>>>>>> Stashed changes

@st.cache_data(ttl=10)
def fetch_class_students(class_id):
    """Fetch students and their stats for a class"""
    try:
        resp = requests.get(
            f"{API_BASE}/classes/{class_id}/students",
            timeout=3
        )
        if resp.ok:
            return resp.json().get("students", [])
    except Exception as e:
        st.error(f"Error fetching students: {e}")
    return []

<<<<<<< Updated upstream
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

    # Class status control
    st.sidebar.markdown("---")
    st.sidebar.subheader("Class Control")
    current_status = fetch_class_status()
    st.sidebar.write(f"**Current Status:** {current_status.upper()}")

    col1, col2 = st.sidebar.columns(2)
    if col1.button("Start Class", disabled=current_status == "active"):
        if set_class_status("active"):
            st.sidebar.success("Class started! Students can now track focus.")
            st.cache_data.clear()
        else:
            st.sidebar.error("Failed to start class")

    if col2.button("Stop Class", disabled=current_status == "inactive"):
        if set_class_status("inactive"):
            st.sidebar.success("Class stopped. Students cannot track focus.")
            st.cache_data.clear()
        else:
            st.sidebar.error("Failed to stop class")

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
=======

def search_users(query):
    """Search for students by email or username"""
    try:
        resp = requests.get(
            f"{API_BASE}/users/search",
            params={"q": query},
            timeout=3
        )
        if resp.ok:
            return resp.json().get("users", [])
    except Exception as e:
        st.error(f"Search error: {e}")
    return []


def student_dashboard():
    """Display student dashboard"""
    st.title(f"Welcome, {st.session_state.username}! 👋")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
    
    st.subheader("Your Scheduled Classes")
    
    classes = fetch_student_classes(st.session_state.user_id)
    
    if not classes:
        st.info("No classes scheduled yet. Ask your teacher to enroll you in a class.")
    else:
        for class_data in classes:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"### {class_data['class_name']}")
                    if class_data.get('scheduled_time'):
                        st.caption(f"📅 {class_data['scheduled_time']}")
                
                with col2:
                    if class_data.get('link'):
                        if st.button("🔗 Join Class", key=f"link_{class_data['id']}"):
                            st.markdown(f"[Click here to join: {class_data['link']}]({class_data['link']})")
                
                with col3:
                    if st.button("▶️ Start Tracking", key=f"start_{class_data['id']}"):
                        st.success(f"Focus tracker activated for {class_data['class_name']}!")
                        st.session_state.active_class_id = class_data['id']
                        st.info(f"Class ID: {class_data['id']} - Share this with the backend tracker")
                
                st.divider()


def teacher_dashboard():
    """Display teacher dashboard"""
    st.title(f"Welcome, {st.session_state.username}! 👨‍🏫")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
    
    # Sidebar for creating new class
    with st.sidebar:
        st.subheader("Create New Class")
        new_class_name = st.text_input("Class Name")
        new_class_time = st.text_input("Scheduled Time (e.g., 2024-04-01 10:00)")
        
        if st.button("Create Class"):
            if new_class_name:
                try:
                    resp = requests.post(
                        f"{API_BASE}/classes",
                        json={
                            "teacher_id": st.session_state.user_id,
                            "class_name": new_class_name,
                            "scheduled_time": new_class_time
                        },
                        timeout=3
                    )
                    if resp.ok:
                        st.success("Class created successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(resp.json().get("error", "Failed to create class"))
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter class name")
    
    st.subheader("Your Classes")
    
    classes = fetch_teacher_classes(st.session_state.user_id)
    
    if not classes:
        st.info("No classes created yet. Create one from the sidebar.")
    else:
        for class_data in classes:
            with st.container():
                st.markdown(f"### {class_data['class_name']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption(f"📅 Scheduled: {class_data.get('scheduled_time', 'TBD')}")
                    
                    # Add meeting link section
                    with st.expander("📎 Add Meeting Link"):
                        current_link = class_data.get('link', '')
                        new_link = st.text_input(
                            "Meeting Link (Zoom, Google Meet, etc.)",
                            value=current_link,
                            key=f"link_input_{class_data['id']}"
                        )
                        if st.button("Save Link", key=f"save_link_{class_data['id']}"):
                            try:
                                resp = requests.post(
                                    f"{API_BASE}/classes/{class_data['id']}/link",
                                    json={"link": new_link},
                                    timeout=3
                                )
                                if resp.ok:
                                    st.success("Link saved!")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Failed to save link")
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    # Add students section
                    with st.expander("👥 Add Students to Class"):
                        st.write("Search for students by email or username")
                        search_query = st.text_input(
                            "Search student",
                            placeholder="Enter email or username",
                            key=f"search_{class_data['id']}"
                        )
                        
                        if search_query and len(search_query) >= 2:
                            users = search_users(search_query)
                            
                            if users:
                                st.write(f"Found {len(users)} student(s):")
                                for user in users:
                                    col_check, col_info = st.columns([0.2, 0.8])
                                    with col_check:
                                        if st.button("➕ Add", key=f"add_{class_data['id']}_{user['id']}"):
                                            try:
                                                resp = requests.post(
                                                    f"{API_BASE}/classes/{class_data['id']}/enroll",
                                                    json={"student_id": user["id"]},
                                                    timeout=3
                                                )
                                                if resp.ok:
                                                    st.success(f"✅ {user['username']} added!")
                                                    st.cache_data.clear()
                                                    st.rerun()
                                                else:
                                                    error_msg = resp.json().get("error", "Failed to add student")
                                                    st.error(f"❌ {error_msg}")
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                    with col_info:
                                        st.caption(f"**{user['username']}** ({user['email']})")
                            else:
                                st.info("No students found with that search")
                
                with col2:
                    st.markdown("**Student Focus Data:**")
                    students = fetch_class_students(class_data['id'])
                    
                    if students:
                        df = pd.DataFrame(students)
                        df['avg_focus'] = df['avg_focus'].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                        st.dataframe(
                            df[['username', 'avg_focus', 'frame_count']],
                            use_container_width=True
                        )
                    else:
                        st.info("No students enrolled yet")
                
                st.divider()
>>>>>>> Stashed changes


def main():
    if not st.session_state.authenticated:
        login_page()
    elif st.session_state.role == "student":
        student_dashboard()
    elif st.session_state.role == "teacher":
        teacher_dashboard()


if __name__ == "__main__":
    main()
