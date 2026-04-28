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
  const [multiDeviceStats, setMultiDeviceStats] = useState(null);
  const [newClass, setNewClass] = useState({ class_name: '', start_time: '', end_time: '', meeting_url: '' });
  const [errors, setErrors] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  useEffect(() => {
    fetchClasses();
  }, []);

  // Auto-refresh selected class stats/history every 5 seconds
  useEffect(() => {
    if (!selectedClass) return;
    const id = selectedClass._id;
    const t = setInterval(() => {
      fetchData(id).catch(() => {});
    }, 5000);
    return () => clearInterval(t);
  }, [selectedClass?._id]);

  const fetchClasses = async () => {
    const token = localStorage.getItem('token');
    const response = await api.get('/classes', { headers: { Authorization: token } });
    setClasses(response.data);
  };

  const fetchData = async (classId) => {
    const token = localStorage.getItem('token');
    const [statsRes, attendanceRes, historyRes, multiDeviceRes] = await Promise.all([
      api.get(`/stats/${classId}`, { headers: { Authorization: token } }),
      api.get(`/attendance/${classId}`, { headers: { Authorization: token } }),
      api.get(`/history/${classId}`, { headers: { Authorization: token } }),
      api.get(`/multi-device-stats/${classId}`, { headers: { Authorization: token } }).catch(() => ({ data: null })) // Fallback for backward compatibility
    ]);
    setStats(statsRes.data);
    setAttendance(attendanceRes.data);
    setHistory(historyRes.data.history.reverse());

    // Set multi-device stats if available
    if (multiDeviceRes.data) {
      setMultiDeviceStats(multiDeviceRes.data);
    }
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

            {multiDeviceStats && (
              <section className="multi-device-section">
                <h2>🔄 Multi-Device Focus Data</h2>
                <div className="multi-device-summary">
                  <div className="summary-card">
                    <h3>Total Students</h3>
                    <p className="stat-value">{multiDeviceStats.total_students}</p>
                  </div>
                  <div className="summary-card">
                    <h3>Class</h3>
                    <p className="stat-value">{multiDeviceStats.class_name}</p>
                  </div>
                </div>

                <div className="device-stats-list">
                  {multiDeviceStats.student_stats?.map((student) => (
                    <div key={student.student_email} className="device-stats-item">
                      <div className="student-header">
                        <strong>{student.student_name}</strong>
                        <span className="student-id">({student.student_id || 'N/A'})</span>
                        <span className="device-count">📱 {student.device_count} device{student.device_count !== 1 ? 's' : ''}</span>
                      </div>

                      <div className="stats-row">
                        <div className="stat-item">
                          <span className="label">Avg Focus:</span>
                          <span className={`value ${student.avg_focus_score >= 7 ? 'high' : student.avg_focus_score >= 4 ? 'medium' : 'low'}`}>
                            {student.avg_focus_score}/10
                          </span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Total Frames:</span>
                          <span className="value">{student.total_frames}</span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Last Activity:</span>
                          <span className="value">
                            {student.latest_activity ? new Date(student.latest_activity).toLocaleString() : 'N/A'}
                          </span>
                        </div>
                      </div>

                      <div className="focus-distribution">
                        <div className="distribution-bar">
                          <div
                            className="bar-segment low"
                            style={{ width: `${(student.focus_distribution.low / student.total_frames) * 100}%` }}
                            title={`Low focus: ${student.focus_distribution.low}`}
                          ></div>
                          <div
                            className="bar-segment medium"
                            style={{ width: `${(student.focus_distribution.medium / student.total_frames) * 100}%` }}
                            title={`Medium focus: ${student.focus_distribution.medium}`}
                          ></div>
                          <div
                            className="bar-segment high"
                            style={{ width: `${(student.focus_distribution.high / student.total_frames) * 100}%` }}
                            title={`High focus: ${student.focus_distribution.high}`}
                          ></div>
                        </div>
                        <div className="distribution-labels">
                          <span>Low: {student.focus_distribution.low}</span>
                          <span>Medium: {student.focus_distribution.medium}</span>
                          <span>High: {student.focus_distribution.high}</span>
                        </div>
                      </div>

                      <div className="behavior-events">
                        <div className="event-item">
                          <span className="event-icon">😴</span>
                          <span>Yawning: {student.behavioral_events.yawning}</span>
                        </div>
                        <div className="event-item">
                          <span className="event-icon">😄</span>
                          <span>Laughing: {student.behavioral_events.laughing}</span>
                        </div>
                        <div className="event-item">
                          <span className="event-icon">😑</span>
                          <span>Eyes Closed: {student.behavioral_events.eyes_closed}</span>
                        </div>
                      </div>

                      <div className="device-list">
                        <strong>Devices:</strong>
                        {student.devices.map((device, idx) => (
                          <span key={idx} className="device-tag">{device}</span>
                        ))}
                      </div>
                    </div>
                  )) || (
                    <div className="empty-card">No multi-device data available yet. Students need to upload their local tracking data.</div>
                  )}
                </div>
              </section>
            )}

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
