import React, { useEffect, useState } from 'react';
import api from '../api';
import './Dashboard.css';

const AdminDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const [requests, setRequests] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user] = useState(JSON.parse(localStorage.getItem('user') || 'null'));

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const [summaryRes, recRes, reqRes] = await Promise.all([
          api.get('/admin/dashboard', { headers: { Authorization: token } }),
          api.get('/admin/recordings', { headers: { Authorization: token } }).catch(() => ({ data: { sessions: [] } })),
          api.get('/admin/recordings/requests', { headers: { Authorization: token } }).catch(() => ({ data: { requests: [] } }))
        ]);
        setSummary(summaryRes.data);
        setRecordings(recRes.data?.sessions || []);
        setRequests(reqRes.data?.requests || []);
      } catch (error) {
        console.error('Failed to load admin dashboard', error);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const approveRequest = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      await api.post(`/admin/recordings/approve/${requestId}`, {}, { headers: { Authorization: token } });
      const reqRes = await api.get('/admin/recordings/requests', { headers: { Authorization: token } });
      setRequests(reqRes.data?.requests || []);
    } catch (e) {
      console.error('Approve failed', e);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1>🛠️ Admin Dashboard</h1>
          <p>Welcome, {user?.name}!</p>
          <button className="logout-btn" onClick={() => { localStorage.clear(); window.location.href = '/'; }}>Logout</button>
        </header>
        <div className="dashboard-content">
          <p>Loading system statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>🛠️ Admin Dashboard</h1>
        <p>Welcome, {user?.name}!</p>
        <button className="logout-btn" onClick={() => { localStorage.clear(); window.location.href = '/'; }}>Logout</button>
      </header>

      <div className="dashboard-content">
        {/* System Users Stats */}
        <section className="stats-section admin-stats">
          <h2>👥 System Users</h2>
          {summary?.system_stats && (
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Users</h3>
                <p className="stat-value">{summary.system_stats.total_users}</p>
              </div>
              <div className="stat-card">
                <h3>Students</h3>
                <p className="stat-value">{summary.system_stats.students}</p>
              </div>
              <div className="stat-card">
                <h3>Teachers</h3>
                <p className="stat-value">{summary.system_stats.teachers}</p>
              </div>
              <div className="stat-card">
                <h3>Admins</h3>
                <p className="stat-value">{summary.system_stats.admins}</p>
              </div>
            </div>
          )}
        </section>

        {/* Classes Overview */}
        <section className="stats-section admin-stats">
          <h2>📚 Classes Overview</h2>
          {summary?.class_stats && (
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Classes</h3>
                <p className="stat-value">{summary.class_stats.total_classes}</p>
              </div>
              <div className="stat-card">
                <h3>Active</h3>
                <p className="stat-value" style={{ color: '#4f46e5' }}>{summary.class_stats.active}</p>
              </div>
              <div className="stat-card">
                <h3>Upcoming</h3>
                <p className="stat-value" style={{ color: '#f59e0b' }}>{summary.class_stats.upcoming}</p>
              </div>
              <div className="stat-card">
                <h3>Completed</h3>
                <p className="stat-value" style={{ color: '#10b981' }}>{summary.class_stats.completed}</p>
              </div>
            </div>
          )}
        </section>

        {/* Tracking Statistics */}
        <section className="stats-section admin-stats">
          <h2>📊 Focus Tracking Statistics</h2>
          {summary?.tracking_stats && (
            <div>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Frames Received</h3>
                  <p className="stat-value">{summary.tracking_stats.total_frames_received}</p>
                </div>
                <div className="stat-card">
                  <h3>Average Class Focus</h3>
                  <p className="stat-value">{summary.tracking_stats.avg_focus_score}/10</p>
                </div>
              </div>

              {/* Behavioral Events */}
              <div className="behavior-summary" style={{ marginTop: '20px' }}>
                <h3>Behavioral Events Summary</h3>
                <div className="stats-grid">
                  <div className="stat-card">
                    <h3>😴 Yawning Events</h3>
                    <p className="stat-value">{summary.tracking_stats.behavioral_events.yawning}</p>
                  </div>
                  <div className="stat-card">
                    <h3>😂 Laughing Events</h3>
                    <p className="stat-value">{summary.tracking_stats.behavioral_events.laughing}</p>
                  </div>
                  <div className="stat-card">
                    <h3>😴 Eyes Closed Events</h3>
                    <p className="stat-value">{summary.tracking_stats.behavioral_events.eyes_closed}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Top Teachers */}
        <section className="stats-section admin-stats">
          <h2>🌟 Top Teachers</h2>
          {summary?.top_teachers && summary.top_teachers.length > 0 ? (
            <div className="top-teachers-list">
              {summary.top_teachers.map((teacher, index) => (
                <div key={teacher.teacher_email} className="teacher-card">
                  <div className="rank-badge">#{index + 1}</div>
                  <div className="teacher-info">
                    <h4>{teacher.teacher_name}</h4>
                    <p className="teacher-email">{teacher.teacher_email}</p>
                  </div>
                  <div className="teacher-stats">
                    <div className="stat-item">
                      <span className="label">Classes:</span>
                      <span className="value">{teacher.total_classes}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Students Taught:</span>
                      <span className="value">{teacher.total_students_taught}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>No teachers have created classes yet.</p>
          )}
        </section>

        <section className="stats-section admin-stats">
          <h2>🎥 Video Recordings</h2>
          {recordings.length === 0 ? (
            <div className="empty-card">No recordings uploaded yet.</div>
          ) : (
            <div className="classes-grid">
              {recordings.map((s) => (
                <div key={s._id} className="class-card" onClick={() => setSelectedSession(s)}>
                  <h3>{s.student_email}</h3>
                  <p>Class: {s.class_id}</p>
                  <p>Status: {s.status}</p>
                  <p>Chunks: {s.chunk_count || 0}</p>
                  <p>Started: {s.started_at ? new Date(s.started_at).toLocaleString() : '-'}</p>
                </div>
              ))}
            </div>
          )}

          {selectedSession && (
            <div style={{ marginTop: 16 }}>
              <h3>Playback (Admin)</h3>
              <video
                controls
                style={{ width: '100%', maxHeight: 420, borderRadius: 12, background: '#111' }}
                src={`${api.defaults.baseURL}/admin/recordings/${selectedSession._id}/video`}
              />
            </div>
          )}
        </section>

        <section className="stats-section admin-stats">
          <h2>📨 Teacher Recording Requests</h2>
          {requests.length === 0 ? (
            <div className="empty-card">No requests.</div>
          ) : (
            <div className="attendance-list">
              {requests.map((r) => (
                <div key={r._id} className="attendance-item">
                  <div>
                    <strong>{r.teacher_email}</strong> requested session <code>{r.session_id}</code>
                    <div style={{ opacity: 0.8, marginTop: 6 }}>
                      Reason: {r.reason || '(none)'} | Status: {r.status}
                    </div>
                  </div>
                  <div>
                    {r.status === 'pending' && (
                      <button className="action-btn" onClick={() => approveRequest(r._id)}>
                        Approve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default AdminDashboard;
