import streamlit as st
import pandas as pd
import requests
import os
import sys
import subprocess
import time
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
            resp = requests.get(url, headers=headers, params=data, timeout=5)
        elif method == 'POST':
            resp = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            raise ValueError(f"Unsupported method: {method}")
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

@st.cache_data(ttl=8)
def fetch_available_classes():
    data = api_request('GET', '/classes/available')
    return data or []

@st.cache_data(ttl=1)
def fetch_categorized_classes():
    data = api_request('GET', '/classes/categorized')
    return data or {'active': [], 'attended': [], 'future': []}

@st.cache_data(ttl=8)
def fetch_attendance(class_id):
    data = api_request('GET', f'/classes/{class_id}/attendance')
    return data.get('attendance', []) if data else []

def login_page():
    st.title("🎓 Student Focus Tracker - Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("📧 Email")
            password = st.text_input("🔐 Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                data = api_request('POST', '/login', {'email': email, 'password': password})
                if data and 'token' in data:
                    st.session_state['token'] = data['token']
                    st.session_state['user'] = data['user']
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                else:
                    st.error("❌ Login failed")

    with tab2:
        with st.form("register_form"):
            email = st.text_input("📧 Email")
            password = st.text_input("🔐 Password", type="password")
            confirm_password = st.text_input("🔐 Confirm Password", type="password")
            name = st.text_input("👤 Name")
            role = st.selectbox("👨‍🎓 Role", ["student", "teacher", "admin"])
            submitted = st.form_submit_button("Register")
            if submitted:
                if password != confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    data = {'email': email, 'password': password, 'name': name, 'role': role}
                    resp = api_request('POST', '/register', data)
                    if resp and 'message' in resp:
                        st.success("✅ Registered successfully! Please login.")
                    else:
                        st.error("❌ Registration failed")

def student_dashboard():
    st.title("👨‍🎓 Student Dashboard")
    user = st.session_state['user']
    st.subheader(f"Welcome, {user['name']}!")

    tab1, tab2, tab3, tab4 = st.tabs(["Available Classes", "My Classes", "Active Classes", "Class History"])

    # Tab 1: Available Classes to Join
    with tab1:
        st.subheader("📚 Available Classes to Join")
        available = fetch_available_classes()
        if available:
            for cls in available:
                with st.expander(f"📖 {cls['class_name']} - by {cls.get('teacher_name', 'Unknown')}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Class ID:** {cls['_id']}")
                        st.write(f"**Teacher:** {cls.get('teacher_name', 'N/A')}")
                        st.write(f"**Students Enrolled:** {cls.get('student_count', 0)}")
                        if cls.get('start_time'):
                            st.write(f"**Start Time:** {cls.get('start_time')}")
                        if cls.get('end_time'):
                            st.write(f"**End Time:** {cls.get('end_time')}")
                    with col2:
                        password = st.text_input("🔐 Class Password", type="password", key=f"join_{cls['_id']}")
                        if st.button("Join Class", key=f"join_btn_{cls['_id']}"):
                            if password:
                                result = api_request('POST', f'/classes/{cls["_id"]}/join', {'password': password})
                                if result and 'message' in result:
                                    st.success("✅ Joined class successfully!")
                                    st.info(f"Starting focus tracker for class {cls['_id']}...")
                                    import subprocess
                                    import sys
                                    # Launch main.py in headless mode (background)
                                    subprocess.Popen([
                                        sys.executable, 
                                        'main.py', 
                                        cls["_id"],
                                        st.session_state.get('token', ''),
                                        '--headless'
                                    ])
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid password")
                            else:
                                st.error("❌ Please enter the class password")
        else:
            st.info("ℹ️ No available classes to join at the moment.")

    # Tab 2: My Classes
    with tab2:
        st.subheader("📚 My Classes")
        classes = api_request('GET', '/classes')
        if classes:
            for cls in classes:
                with st.expander(f"📖 {cls['class_name']} - by {cls.get('teacher_name', 'Unknown')} ({cls.get('status', 'unknown').upper()})"):
                    st.write(f"**Class ID:** {cls['_id']}")
                    st.write(f"**Teacher:** {cls.get('teacher_name', 'N/A')}")
                    st.write(f"**Status:** {cls.get('status', 'N/A')}")
                    if cls.get('start_time'):
                        st.write(f"**Start Time:** {cls.get('start_time')}")
                    if cls.get('end_time'):
                        st.write(f"**End Time:** {cls.get('end_time')}")
                    
                    meeting_url = cls.get('meeting_url')
                    if meeting_url:
                        st.write(f"**Meeting URL:** [Join Meeting]({meeting_url})")
                    else:
                        st.info("ℹ️ Teacher has not posted the meeting link yet.")
        else:
            st.info("ℹ️ You are not enrolled in any classes yet.")

    # Tab 3: Active Classes (with tracking)
    with tab3:
        st.subheader("🎥 Active Classes - Start Tracking")
        categorized = fetch_categorized_classes()
        active_classes = categorized.get('active', [])
    # Initialize tracking state in session
    if 'active_trackers' not in st.session_state:
        st.session_state.active_trackers = {}
    if 'joined_classes' not in st.session_state:
        st.session_state.joined_classes = set()
    
    with tab3:
        col_title, col_refresh = st.columns([5, 1])
        with col_title:
            st.subheader("🎥 Active Classes")
        with col_refresh:
            if st.button("🔄 Refresh", key="refresh_student_active"):
                st.cache_data.clear()
                st.rerun()
        
        if active_classes:
            for cls in active_classes:
                with st.expander(f"🔴 {cls['class_name']} - LIVE", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Teacher:** {cls.get('teacher_name', 'N/A')}")
                        st.write(f"**Class ID:** {cls['_id'][:8]}...")
                        meeting_url = cls.get('meeting_url')
                        if meeting_url:
                            st.markdown(f"[🔗 Join Meeting]({meeting_url})")
                    
                    with col2:
                        stats = fetch_stats(cls['_id'])
                        st.metric("Your Focus", f"{stats.get('average_score', 0.0):.1f}%")
                    
                    class_id = cls['_id']
                    token = st.session_state.get('token', '')
                    user = st.session_state.get('user', {})
                    student_email = user.get('email', '')
                    
                    # Check if student is enrolled in this class
                    is_enrolled = student_email in cls.get('enrolled_students', [])
                    is_tracking = class_id in st.session_state.active_trackers and \
                                 st.session_state.active_trackers[class_id] is not None and \
                                 st.session_state.active_trackers[class_id].poll() is None
                    
                    if not is_enrolled:
                        # Show Join Class button
                        st.info("ℹ️ You need to join this class to participate and start tracking.")
                        if st.button("✅ Join Class", key=f"join_active_class_{class_id}"):
                            # Call join endpoint (no password needed for active classes)
                            result = api_request('POST', f'/classes/{class_id}/join', {
                                'password': cls.get('class_password', '')
                            })
                            if result and 'message' in result:
                                st.success("✅ Successfully joined the class!")
                                st.session_state.joined_classes.add(class_id)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Failed to join class. Try again.")
                    else:
                        # Student is enrolled - show tracking controls
                        if not is_tracking:
                            # Auto-start tracking
                            try:
                                process = subprocess.Popen([
                                    sys.executable,
                                    'main.py',
                                    class_id,
                                    token,
                                    '--headless'
                                ])
                                st.session_state.active_trackers[class_id] = process
                                is_tracking = True
                            except Exception as e:
                                st.error(f"❌ Failed to auto-launch tracker: {e}")
                        
                        if is_tracking:
                            st.success("✅ **🎥 Tracking Active!** - Your camera is being monitored and data is being stored.")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("⏹️ Stop Tracking", key=f"stop_track_{class_id}"):
                                    try:
                                        if class_id in st.session_state.active_trackers:
                                            process = st.session_state.active_trackers[class_id]
                                            if process and process.poll() is None:
                                                process.terminate()
                                                process.wait(timeout=2)
                                            st.session_state.active_trackers[class_id] = None
                                            st.info("⏹️ Tracking stopped.")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error stopping tracker: {e}")
                            with col2:
                                st.caption("📹 Focus data is being captured and stored automatically")
                        else:
                            st.warning("⚠️ Tracking process has stopped")
        else:
            st.info("ℹ️ No active classes right now.")

    # Tab 4: Class History
    with tab4:
        st.subheader("📊 Your Class History")
        classes = api_request('GET', '/classes')
        if classes:
            class_dict = {cls['_id']: cls['class_name'] for cls in classes}
            selected_class_id = st.selectbox("Select a class", list(class_dict.keys()), format_func=lambda x: class_dict[x])
            
            history = fetch_history(selected_class_id)
            if not history.empty:
                user_history = history[history['student_email'] == user['email']]
                if not user_history.empty:
                    st.write("**Your Focus Score Over Time:**")
                    st.line_chart(user_history.set_index("timestamp")["focus_score"])
                    
                    st.write("**Statistics:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg Focus", f"{user_history['focus_score'].mean():.1f}%")
                    with col2:
                        st.metric("Max Focus", f"{user_history['focus_score'].max():.1f}%")
                    with col3:
                        st.metric("Min Focus", f"{user_history['focus_score'].min():.1f}%")
                else:
                    st.info("ℹ️ No focus data for this class yet.")
            else:
                st.info("ℹ️ No history available for this class.")

def teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    user = st.session_state['user']
    st.subheader(f"Welcome, {user['name']}!")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Active Classes", "Upcoming Classes", "Completed Classes", "Create Class", "Analytics"])

    categorized = fetch_categorized_classes()
    active_classes = categorized.get('active', [])
    future_classes = categorized.get('future', [])
    attended_classes = categorized.get('attended', [])

    # Tab 1: Active Classes
    with tab1:
        col_title, col_refresh = st.columns([5, 1])
        with col_title:
            st.subheader("🔴 Active Classes - Real-Time Dashboard")
        with col_refresh:
            if st.button("🔄 Refresh", key="refresh_active"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
        
        if active_classes:
            for cls in active_classes:
                with st.expander(f"🎥 {cls['class_name']} - NOW LIVE", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Class ID:** {cls['_id']}")
                        st.write(f"**Students:** {len(cls.get('enrolled_students', []))}")
                    
                    with col2:
                        meeting_url = st.text_input("📎 Meeting URL", value=cls.get('meeting_url', ''), key=f"meeting_{cls['_id']}")
                        if st.button("📤 Post Meeting Link", key=f"post_link_{cls['_id']}"):
                            if meeting_url:
                                result = api_request('POST', f'/classes/{cls["_id"]}/meeting-link', {'meeting_url': meeting_url})
                                if result and 'message' in result:
                                    st.success("✅ Meeting link posted!")
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.error("❌ Please enter a meeting URL")
                    
                    with col3:
                        if st.button("❌ End Class", key=f"stop_{cls['_id']}"):
                            resp = api_request('POST', f'/classes/{cls["_id"]}/status', {'status': 'completed'})
                            if resp and 'message' in resp:
                                st.success("✅ Class ended!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Failed to end class")

                    st.divider()

                    # Class Stats
                    stats = fetch_stats(cls['_id'])
                    active_count = fetch_active_students(cls['_id']).get('active_students', 0)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🟢 Currently Active", active_count)
                    with col2:
                        st.metric("📊 Class Avg Focus", f"{stats.get('average_score', 0.0):.1f}%")
                    with col3:
                        st.metric("📈 Total Records", stats.get('count', 0))

                    st.divider()

                    # Low Attention Alerts
                    low_alerts = api_request('GET', f'/classes/{cls["_id"]}/low-attention-alerts')
                    if low_alerts and low_alerts.get('alerts'):
                        st.warning("🔴 **LOW ATTENTION ALERTS** (< 30%)")
                        alert_cols = st.columns(len(low_alerts.get('alerts', [])))
                        for idx, alert_student in enumerate(low_alerts.get('alerts', [])):
                            with alert_cols[idx % len(alert_cols)]:
                                st.error(f"⚠️ {alert_student['student_name']}\n**{alert_student['avg_attention']}%**")
                    
                    st.divider()

                    # STUDENT ATTENTION DASHBOARD
                    st.write("### 📊 **Student Attention Dashboard**")
                    
                    attendance = fetch_attendance(cls['_id'])
                    history = fetch_history(cls['_id'])
                    
                    if attendance:
                        # Create student attention cards with mini-charts
                        student_cols = st.columns(min(len(attendance), 4) if attendance else 1)
                        
                        for idx, student in enumerate(attendance):
                            with student_cols[idx % len(student_cols)]:
                                student_email = student.get('student_email', '')
                                student_name = student.get('student_name', 'Unknown')
                                avg_attention = student.get('avg_attention', 0)
                                
                                # Color code based on attention
                                if avg_attention >= 70:
                                    color = "🟢"
                                    status = "Excellent"
                                elif avg_attention >= 50:
                                    color = "🟡"
                                    status = "Good"
                                elif avg_attention >= 30:
                                    color = "🟠"
                                    status = "Fair"
                                else:
                                    color = "🔴"
                                    status = "Low"
                                
                                with st.container(border=True):
                                    st.markdown(f"{color} **{student_name}**")
                                    st.metric("Attention %", f"{avg_attention:.1f}%", label_visibility="collapsed")
                                    st.caption(f"Status: {status} | Frames: {student.get('frames_sent', 0)}")
                        
                        st.divider()
                        
                        # Per-student attention trend graphs (only if history exists)
                        if not history.empty:
                            st.write("### 📈 **Individual Student Trends**")
                            
                            # Ensure student_email column exists in history
                            if 'student_email' not in history.columns:
                                st.info("⏳ Collecting focus data for students...")
                            else:
                                graph_cols = st.columns(min(len(attendance), 2))
                                for idx, student in enumerate(attendance):
                                    student_email = student.get('student_email', '')
                                    student_name = student.get('student_name', 'Unknown')
                                    
                                    # Filter history for this student
                                    student_history = history[history['student_email'] == student_email] if student_email else None
                                    
                                    with graph_cols[idx % 2]:
                                        st.write(f"**{student_name}'s Focus Trend**")
                                        if student_history is not None and not student_history.empty and 'focus_score' in student_history.columns:
                                            chart_data = student_history[['timestamp', 'focus_score']].copy()
                                            chart_data = chart_data.set_index('timestamp')
                                            st.area_chart(chart_data, color="#00D084" if student.get('avg_attention', 0) >= 50 else "#FF6B6B")
                                        else:
                                            st.caption(f"No focus data yet")
                        
                        st.divider()
                        
                        # Full Attendance Table
                        st.write("**📋 Complete Attendance Report:**")
                        att_df = pd.DataFrame(attendance)
                        display_cols = ['student_name', 'attended', 'avg_attention', 'frames_sent']
                        available_cols = [col for col in display_cols if col in att_df.columns]
                        st.dataframe(att_df[available_cols], use_container_width=True)
                    else:
                        st.info("⏳ Waiting for students to join and start tracking...")
                    
                    # Overall Class Trend
                    st.write("**📊 Overall Class Focus Trend:**")
                    if not history.empty:
                        st.line_chart(history.set_index("timestamp")["focus_score"])
                    else:
                        st.info("No focus data yet")
        else:
            st.info("ℹ️ No active classes right now.")

    # Tab 2: Upcoming Classes
    with tab2:
        st.subheader("🕐 Upcoming Classes")
        if future_classes:
            for cls in future_classes:
                with st.expander(f"📅 {cls['class_name']} - {cls.get('start_time', 'TBD')}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**Class ID:** {cls['_id']}")
                        st.write(f"**Start:** {cls.get('start_time', 'N/A')}")
                        st.write(f"**End:** {cls.get('end_time', 'N/A')}")
                        st.write(f"**Enrolled Students:** {len(cls.get('enrolled_students', []))}")
                    
                    with col2:
                        meeting_url = st.text_input("📎 Meeting URL", value=cls.get('meeting_url', ''), key=f"meeting_upcoming_{cls['_id']}")
                        if st.button("📤 Post Link", key=f"post_link_upcoming_{cls['_id']}"):
                            if meeting_url:
                                result = api_request('POST', f'/classes/{cls["_id"]}/meeting-link', {'meeting_url': meeting_url})
                                if result:
                                    st.success("✅ Link posted!")
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.error("Enter URL first")
                    
                    with col3:
                        if st.button("▶️ START", key=f"start_class_{cls['_id']}", help="Start the class now"):
                            with st.spinner("🔄 Starting class..."):
                                response = api_request('POST', f'/classes/{cls["_id"]}/start', {})
                                if response:
                                    st.success("✅ Class started successfully!")
                                    st.info("📣 Students have been notified. Refreshing dashboard...")
                                    
                                    # Clear all caches aggressively
                                    for key in list(st.session_state.keys()):
                                        if 'cache' in str(key).lower():
                                            del st.session_state[key]
                                    
                                    st.cache_data.clear()
                                    st.cache_resource.clear()
                                    
                                    # Wait for backend to process
                                    import time
                                    time.sleep(1.5)
                                    
                                    # Force a complete rerun
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to start class")
        else:
            st.info("ℹ️ No upcoming classes scheduled.")

    # Tab 3: Completed Classes
    with tab3:
        st.subheader("✅ Completed Classes")
        if attended_classes:
            for cls in attended_classes:
                with st.expander(f"✔️ {cls['class_name']}"):
                    st.write(f"**Class ID:** {cls['_id']}")
                    st.write(f"**Scheduled:** {cls.get('start_time')} to {cls.get('end_time')}")
                    
                    stats = fetch_stats(cls['_id'])
                    attendance = fetch_attendance(cls['_id'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Final Avg Focus", f"{stats.get('average_score', 0.0):.1f}%")
                    with col2:
                        if attendance:
                            attended_count = sum(1 for a in attendance if a.get('attended'))
                            st.metric("👥 Attended", f"{attended_count}/{len(attendance)}")
                    with col3:
                        st.metric("📈 Total Records", stats.get('count', 0))

                    # Attendance Report with Average Attention
                    st.write("**📋 Final Attendance & Focus Report:**")
                    if attendance:
                        att_df = pd.DataFrame(attendance)
                        # Display relevant columns
                        display_cols = ['student_name', 'attended', 'avg_attention', 'frames_sent']
                        st.dataframe(att_df[display_cols].rename(columns={
                            'avg_attention': 'Avg Attention %',
                            'student_name': 'Student',
                            'attended': 'Attended',
                            'frames_sent': 'Frames'
                        }), use_container_width=True)
                    
                    # Final Chart
                    history = fetch_history(cls['_id'])
                    if not history.empty:
                        st.write("**📊 Final Focus Data:**")
                        st.line_chart(history.set_index("timestamp")["focus_score"])
        else:
            st.info("ℹ️ No completed classes yet.")

    # Tab 4: Create Class
    with tab4:
        st.subheader("➕ Create New Class")
        with st.form("create_class_form"):
            class_name = st.text_input("📚 Class Name", placeholder="e.g., Python 101 - Lecture 5")
            class_password = st.text_input("🔐 Class Password", type="password", placeholder="Students will use this to join")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("📅 Start Date")
                start_time = st.time_input("⏰ Start Time")
            with col2:
                end_date = st.date_input("📅 End Date")
                end_time = st.time_input("⏰ End Time")
            
            submitted = st.form_submit_button("✅ Create Class")
            if submitted:
                if not class_name:
                    st.error("❌ Class name is required")
                elif not class_password:
                    st.error("❌ Class password is required")
                else:
                    start_datetime = datetime.combine(start_date, start_time).isoformat()
                    end_datetime = datetime.combine(end_date, end_time).isoformat()
                    data = {
                        'class_name': class_name,
                        'class_password': class_password,
                        'start_time': start_datetime,
                        'end_time': end_datetime
                    }
                    resp = api_request('POST', '/classes', data)
                    if resp and 'class_id' in resp:
                        st.success(f"✅ Class created! ID: {resp['class_id']}")
                        st.info("Students can now see this class in 'Available Classes' and join with the password you set.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ Failed to create class")

    # Tab 5: Analytics
    with tab5:
        st.subheader("📈 Overall Analytics")
        all_classes = active_classes + future_classes + attended_classes
        
        if all_classes:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📚 Total Classes", len(all_classes))
            with col2:
                st.metric("🔴 Active", len(active_classes))
            with col3:
                st.metric("✅ Completed", len(attended_classes))
            
            st.write("---")
            st.write("**📊 Class Performance Summary:**")
            
            class_stats = []
            for cls in all_classes:
                stats = fetch_stats(cls['_id'])
                attendance = fetch_attendance(cls['_id'])
                class_stats.append({
                    'Class': cls['class_name'],
                    'Status': cls.get('status', 'N/A'),
                    'Avg Focus': f"{stats.get('average_score', 0.0):.1f}%",
                    'Records': stats.get('count', 0),
                    'Attendance': f"{sum(1 for a in attendance if a.get('attended'))}/{len(attendance)}"
                })
            
            if class_stats:
                stats_df = pd.DataFrame(class_stats)
                st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("ℹ️ No classes created yet.")

def main():
    st.set_page_config(page_title="Student Focus Tracker", layout="wide", initial_sidebar_state="collapsed")
    
    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Not logged in
    if not st.session_state['token']:
        login_page()
    else:
        # Logged in - show appropriate dashboard
        user = st.session_state['user']
        
        # Sidebar
        with st.sidebar:
            st.title("🎓 Focus Tracker")
            st.write(f"**{user['name']}** ({user['role']})")
            st.divider()
            
            if st.button("🚪 Logout"):
                st.session_state['token'] = None
                st.session_state['user'] = None
                st.cache_data.clear()
                st.rerun()

        # Route to appropriate dashboard
        if user['role'] == 'student':
            student_dashboard()
        elif user['role'] == 'teacher':
            teacher_dashboard()
        else:
            st.error("Unknown role")

if __name__ == "__main__":
    main()