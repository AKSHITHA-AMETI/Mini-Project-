import React, { useState, useEffect } from 'react';
import api from '../api';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import './Dashboard.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const TeacherDashboard = () => {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [stats, setStats] = useState({});
  const [attendance, setAttendance] = useState([]);
  const [history, setHistory] = useState([]);
  const [newClass, setNewClass] = useState({ class_name: '', start_time: '', end_time: '', meeting_url: '' });
  const [errors, setErrors] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    const token = localStorage.getItem('token');
    const response = await api.get('/classes', { headers: { Authorization: token } });
    setClasses(response.data);
  };

  const fetchData = async (classId) => {
    const token = localStorage.getItem('token');
    const [statsRes, attendanceRes, historyRes] = await Promise.all([
      api.get(`/stats/${classId}`, { headers: { Authorization: token } }),
      api.get(`/attendance/${classId}`, { headers: { Authorization: token } }),
      api.get(`/history/${classId}`, { headers: { Authorization: token } }),
    ]);
    setStats(statsRes.data);
    setAttendance(attendanceRes.data);
    setHistory(historyRes.data.history.reverse());
  };

  const copyJoinLink = async (classId) => {
    const joinUrl = `${window.location.origin}/student?join=${classId}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(joinUrl);
        alert('Student join link copied to clipboard! Share this URL with students.');
        return;
      } catch (err) {
        console.warn('Clipboard write failed:', err);
      }
    }
    prompt('Copy this student join link:', joinUrl);
  };

  const handleClassSelect = (cls) => {
    setSelectedClass(cls);
    fetchData(cls._id);
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    if (!newClass.class_name || !newClass.start_time || !newClass.end_time) {
      setErrors('Class name, start time, and end time are required.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await api.post('/classes', newClass, { headers: { Authorization: token } });
      setNewClass({ class_name: '', start_time: '', end_time: '', meeting_url: '' });
      setErrors('');
      setStatusMessage('Class created successfully.');
      fetchClasses();
    } catch (err) {
      setErrors(err.response?.data?.error || 'Failed to create class');
    }
  };

  const chartData = {
    labels: history.map((h) => new Date(h.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Focus Score',
        data: history.map((h) => h.focus_score),
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Class Focus Trend' },
    },
    scales: {
      y: { beginAtZero: true, max: 10 },
    },
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>👨‍🏫 Teacher Dashboard</h1>
        <p>Welcome, {user?.name}!</p>
        <button className="logout-btn" onClick={() => { localStorage.clear(); window.location.href = '/'; }}>Logout</button>
      </header>

      <div className="dashboard-content">
        <section className="classes-section">
          <h2>📚 My Classes</h2>
          <div className="classes-grid">
            {classes.length === 0 ? (
              <div className="class-card empty-card">
                <p>No classes created yet. Create one below.</p>
              </div>
            ) : classes.map((cls) => (
              <div key={cls._id} className="class-card" onClick={() => handleClassSelect(cls)}>
                <h3>{cls.class_name}</h3>
                <p>Status: {cls.status}</p>
                <p>Students: {cls.student_emails?.length || 0}</p>
                <p>Start: {new Date(cls.start_time).toLocaleString()}</p>
                <button
                  type="button"
                  className="action-btn"
                  onClick={(e) => { e.stopPropagation(); copyJoinLink(cls._id); }}
                >
                  Copy Student Join Link
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="create-class-section">
          <h2>➕ Create Class</h2>
          <form className="create-class-form" onSubmit={handleCreateClass}>
            <div className="form-group">
              <label>Class Name</label>
              <input
                type="text"
                value={newClass.class_name}
                onChange={(e) => setNewClass({ ...newClass, class_name: e.target.value })}
                className="form-input"
                placeholder="Course name"
              />
            </div>
            <div className="form-group">
              <label>Start Time (IST)</label>
              <input
                type="datetime-local"
                value={newClass.start_time}
                onChange={(e) => setNewClass({ ...newClass, start_time: e.target.value })}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>End Time (IST)</label>
              <input
                type="datetime-local"
                value={newClass.end_time}
                onChange={(e) => setNewClass({ ...newClass, end_time: e.target.value })}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Meeting URL</label>
              <input
                type="text"
                value={newClass.meeting_url}
                onChange={(e) => setNewClass({ ...newClass, meeting_url: e.target.value })}
                className="form-input"
                placeholder="https://..."
              />
            </div>
            {errors && <p className="form-error">{errors}</p>}
            {statusMessage && <p className="status-banner">{statusMessage}</p>}
            <button type="submit" className="action-btn">Create Class</button>
          </form>
        </section>

        {selectedClass && (
          <div>
            <section className="stats-section">
              <h2>📊 Class Statistics</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Average Focus</h3>
                  <p className="stat-value">{stats.average?.toFixed(1) || 0}/10</p>
                </div>
                <div className="stat-card">
                  <h3>Total Records</h3>
                  <p className="stat-value">{stats.count || 0}</p>
                </div>
              </div>
            </section>

            <section className="attendance-section">
              <h2>👥 Attendance</h2>
              <div className="attendance-list">
                {attendance.length === 0 ? (
                  <div className="empty-card">No attendance data yet.</div>
                ) : attendance.map((student) => (
                  <div key={student.student_email} className="attendance-item">
                    <div>
                      <strong>{student.student_name}</strong> ({student.student_id || 'N/A'})
                    </div>
                    <div className="attendance-details">
                      <span className={student.attended ? 'present' : 'absent'}>
                        {student.attended ? '✅ Present' : '❌ Absent'}
                      </span>
                      <span>Avg Focus: {student.avg_attention?.toFixed(1) || 0}/10</span>
                      <span>{student.last_seen ? `Last seen: ${new Date(student.last_seen).toLocaleTimeString()}` : 'No data'}</span>
                      {student.inactive && <span className="inactive-note">Inactive</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="chart-section">
              <h2>📈 Focus Trend</h2>
              <div className="chart-container">
                <Line data={chartData} options={chartOptions} />
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeacherDashboard;
