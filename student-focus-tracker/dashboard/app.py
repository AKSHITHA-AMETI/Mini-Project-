import streamlit as st
import pandas as pd
import requests
import os
import webbrowser
from datetime import datetime

try:
    API_BASE = st.secrets["api_base"]
except:
    API_BASE = os.getenv("FOCUS_API_URL", "http://127.0.0.1:5000")

def api_request(method, endpoint, data=None, headers=None):
    url = f"{API_BASE}{endpoint}"
    if headers is None:
        headers = {}
    if 'token' in st.session_state:
        headers['Authorization'] = st.session_state['token']
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=3)
        elif method == 'POST':
            resp = requests.post(url, json=data, headers=headers, timeout=3)
        if resp.ok:
            return resp.json()
        else:
            st.error(f"API Error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None

@st.cache_data(ttl=8)
def fetch_history(class_id, limit=240):
    data = api_request('GET', f'/history/{class_id}', {'limit': limit})
    if data:
        df = pd.DataFrame(data.get("history", []))
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.sort_values("timestamp", inplace=True)
        return df
    return pd.DataFrame()

@st.cache_data(ttl=5)
def fetch_stats(class_id):
    data = api_request('GET', f'/stats/{class_id}')
    return data or {}

@st.cache_data(ttl=5)
def fetch_active_students(class_id):
    data = api_request('GET', f'/active_students/{class_id}')
    return data or {'active_students': 0}

def login_page():
    st.title("Student Focus Tracker - Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                data = api_request('POST', '/login', {'email': email, 'password': password})
                if data and 'token' in data:
                    st.session_state['token'] = data['token']
                    st.session_state['user'] = data['user']
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Login failed")

    with tab2:
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            name = st.text_input("Name")
            role = st.selectbox("Role", ["student", "teacher", "admin"])
            class_name = st.text_input("Class Name (for students)") if role == "student" else ""
            submitted = st.form_submit_button("Register")
            if submitted:
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    data = {'email': email, 'password': password, 'name': name, 'role': role}
                    if role == "student":
                        data['class_name'] = class_name
                    resp = api_request('POST', '/register', data)
                    if resp and 'message' in resp:
                        st.success("Registered successfully! Please login.")
                    else:
                        st.error("Registration failed")

def student_page():
    st.title("Student Dashboard")
    user = st.session_state['user']
    st.subheader(f"Welcome, {user['name']}")

    # Get classes for student
    classes = api_request('GET', '/classes')
    active_classes = [cls for cls in classes if cls.get('status') == 'active'] if classes else []
    if active_classes:
        class_options = {cls['_id']: cls['class_name'] for cls in active_classes}
        selected_class = st.selectbox("Select Active Class", list(class_options.keys()), format_func=lambda x: class_options[x])
        class_id = selected_class

        # Check class status
        cls = next((c for c in active_classes if c['_id'] == class_id), None)
        if cls and cls['status'] == 'active':
            st.success("Class is active. Tracking is enabled.")
            meeting_url = cls.get('meeting_url')
            if meeting_url:
                st.write(f"**Class Meeting URL:** {meeting_url}")
                st.info("You must join through this official class URL provided by your teacher.")
                if st.button("Join Meeting & Start Tracking"):
                    st.success(f"Opening meeting: {meeting_url}")
                    st.info("Focus tracking will start automatically. Keep this window open.")
                    webbrowser.open(meeting_url)
                    st.session_state["tracking"] = True
            else:
                st.warning("No meeting URL provided by teacher.")
        else:
            st.warning("Class is not active.")

        # Show personal stats
        stats = fetch_stats(class_id)
        if stats:
            col1, col2 = st.columns(2)
            col1.metric("Your Average Focus", f"{stats.get('average_score', 0.0):.1f}%")
            if stats.get("latest") and stats['latest'].get('student_email') == user['email']:
                col2.metric("Your Latest Score", f"{stats['latest'].get('focus_score', 0.0):.1f}%")

        # History
        history = fetch_history(class_id)
        if not history.empty:
            user_history = history[history['student_email'] == user['email']]
            if not user_history.empty:
                st.subheader("Your Focus History")
                st.line_chart(user_history.set_index("timestamp")["focus_score"])
    else:
        st.warning("No active classes available.")

def teacher_page():
    st.title("Teacher Dashboard")
    user = st.session_state['user']
    st.subheader(f"Welcome, {user['name']}")

    tab1, tab2, tab3 = st.tabs(["Active Classes", "Create Class", "Completed Classes"])

    with tab2:
        with st.form("create_class"):
            class_name = st.text_input("Class Name")
            student_emails = st.text_area("Student Emails (comma separated)")
            meeting_url = st.text_input("Meeting URL", placeholder="https://meet.google.com/abc-defg-hij")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
                start_time = st.time_input("Start Time")
            with col2:
                end_date = st.date_input("End Date")
                end_time = st.time_input("End Time")
            submitted = st.form_submit_button("Create Class")
            if submitted:
                from datetime import datetime
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)
                start_time_str = start_datetime.isoformat()
                end_time_str = end_datetime.isoformat()
                emails = [e.strip() for e in student_emails.split(',')]
                data = {
                    'class_name': class_name,
                    'student_emails': emails,
                    'meeting_url': meeting_url,
                    'start_time': start_time_str,
                    'end_time': end_time_str
                }
                resp = api_request('POST', '/classes', data)
                if resp and 'message' in resp:
                    st.success("Class created!")
                    st.cache_data.clear()
                else:
                    st.error("Failed to create class")

    with tab1:
        classes = api_request('GET', '/classes')
        active_classes = [cls for cls in classes if cls.get('status') == 'active'] if classes else []
        if active_classes:
            for cls in active_classes:
                with st.expander(f"{cls['class_name']} - ACTIVE"):
                    start_dt = pd.to_datetime(cls['start_time']).strftime("%Y-%m-%d %H:%M")
                    end_dt = pd.to_datetime(cls['end_time']).strftime("%Y-%m-%d %H:%M")
                    st.write(f"Start: {start_dt}, End: {end_dt}")
                    st.write(f"Meeting URL: {cls.get('meeting_url', 'Not set')}")
                    st.write(f"Students: {', '.join(cls['student_emails'])}")
                    col1, col2, col3 = st.columns(3)
                    if col1.button(f"Stop Class", key=f"stop_{cls['_id']}"):
                        api_request('POST', f'/classes/{cls["_id"]}/status', {'status': 'inactive'})
                        st.cache_data.clear()
                        st.rerun()
                    if col2.button(f"Complete Class", key=f"complete_{cls['_id']}"):
                        api_request('POST', f'/classes/{cls["_id"]}/status', {'status': 'completed'})
                        st.cache_data.clear()
                        st.rerun()
                    if col3.button(f"Refresh", key=f"refresh_{cls['_id']}"):
                        st.cache_data.clear()
                        st.rerun()

                    # Class stats
                    stats = fetch_stats(cls['_id'])
                    active = fetch_active_students(cls['_id'])
                    st.metric("Active Students", active['active_students'])
                    st.metric("Average Focus", f"{stats.get('average_score', 0.0):.1f}%")

                    history = fetch_history(cls['_id'])
                    if not history.empty:
                        st.line_chart(history.set_index("timestamp")["focus_score"])

                        st.subheader("Individual Student Dashboards")
                        for email in cls['student_emails']:
                            student_data = history[history['student_email'] == email]
                            if not student_data.empty:
                                avg_focus = student_data['focus_score'].mean()
                                st.write(f"**{email}**: Average Focus {avg_focus:.1f}%")
                                st.line_chart(student_data.set_index("timestamp")["focus_score"])

    with tab3:
        completed_classes = [cls for cls in classes if cls.get('status') == 'completed'] if classes else []
        if completed_classes:
            for cls in completed_classes:
                with st.expander(f"{cls['class_name']} - COMPLETED"):
                    start_dt = pd.to_datetime(cls['start_time']).strftime("%Y-%m-%d %H:%M")
                    end_dt = pd.to_datetime(cls['end_time']).strftime("%Y-%m-%d %H:%M")
                    st.write(f"Start: {start_dt}, End: {end_dt}")
                    st.write(f"Meeting URL: {cls.get('meeting_url', 'Not set')}")
                    st.write(f"Students: {', '.join(cls['student_emails'])}")

                    # Final stats
                    stats = fetch_stats(cls['_id'])
                    st.metric("Total Records", stats.get('count', 0))
                    st.metric("Final Average Focus", f"{stats.get('average_score', 0.0):.1f}%")

                    history = fetch_history(cls['_id'])
                    if not history.empty:
                        st.line_chart(history.set_index("timestamp")["focus_score"])
                        st.subheader("Full History")
                        st.dataframe(history)

                        st.subheader("Individual Student Dashboards")
                        for email in cls['student_emails']:
                            student_data = history[history['student_email'] == email]
                            if not student_data.empty:
                                avg_focus = student_data['focus_score'].mean()
                                st.write(f"**{email}**: Average Focus {avg_focus:.1f}%")
                                st.line_chart(student_data.set_index("timestamp")["focus_score"])
        else:
            st.info("No completed classes.")

def admin_page():
    st.title("Admin Dashboard")
    user = st.session_state['user']
    st.subheader(f"Welcome, {user['name']}")

    # Monitor all classes
    classes = api_request('GET', '/classes')
    if classes:
        active_classes = [cls for cls in classes if cls.get('status') == 'active']
        completed_classes = [cls for cls in classes if cls.get('status') == 'completed']

        st.subheader("Active Classes")
        if active_classes:
            for cls in active_classes:
                with st.expander(f"{cls['class_name']} - {cls['teacher_email']}"):
                    stats = fetch_stats(cls['_id'])
                    active = fetch_active_students(cls['_id'])
                    st.metric("Active Students", active['active_students'])
                    st.metric("Average Focus", f"{stats.get('average_score', 0.0):.1f}%")

                    history = fetch_history(cls['_id'])
                    if not history.empty:
                        st.line_chart(history.set_index("timestamp")["focus_score"])

                        st.subheader("Individual Student Dashboards")
                        for email in cls['student_emails']:
                            student_data = history[history['student_email'] == email]
                            if not student_data.empty:
                                avg_focus = student_data['focus_score'].mean()
                                st.write(f"**{email}**: Average Focus {avg_focus:.1f}%")
                                st.line_chart(student_data.set_index("timestamp")["focus_score"])
        else:
            st.info("No active classes.")

        st.subheader("Completed Classes")
        if completed_classes:
            for cls in completed_classes:
                with st.expander(f"{cls['class_name']} - {cls['teacher_email']}"):
                    stats = fetch_stats(cls['_id'])
                    st.metric("Total Records", stats.get('count', 0))
                    st.metric("Final Average Focus", f"{stats.get('average_score', 0.0):.1f}%")

                    history = fetch_history(cls['_id'])
                    if not history.empty:
                        st.line_chart(history.set_index("timestamp")["focus_score"])

                        st.subheader("Individual Student Dashboards")
                        for email in cls['student_emails']:
                            student_data = history[history['student_email'] == email]
                            if not student_data.empty:
                                avg_focus = student_data['focus_score'].mean()
                                st.write(f"**{email}**: Average Focus {avg_focus:.1f}%")
                                st.line_chart(student_data.set_index("timestamp")["focus_score"])
        else:
            st.info("No completed classes.")
    else:
        st.warning("No classes.")

def main():
    if 'token' not in st.session_state:
        login_page()
    else:
        user = st.session_state['user']
        role = user['role']

        if role == "student":
            student_page()
        elif role == "teacher":
            teacher_page()
        else:
            admin_page()

        if st.sidebar.button("Logout"):
            del st.session_state['token']
            del st.session_state['user']
            st.rerun()

if __name__ == "__main__":
    main()
