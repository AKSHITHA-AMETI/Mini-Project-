import React, { useEffect, useState } from 'react';
import api from '../api';
import './Dashboard.css';

const AdminDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [user] = useState(JSON.parse(localStorage.getItem('user') || 'null'));

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await api.get('/admin/summary', {
          headers: { Authorization: token }
        });
        setSummary(response.data);
      } catch (error) {
        console.error('Failed to load admin summary', error);
      }
    };
    fetchSummary();
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>🛠️ Admin Dashboard</h1>
        <p>Welcome, {user?.name}!</p>
        <button className="logout-btn" onClick={() => { localStorage.clear(); window.location.href = '/'; }}>Logout</button>
      </header>

      <div className="dashboard-content">
        <section className="stats-section admin-stats">
          <h2>📌 System Overview</h2>
          {summary ? (
            <div className="stats-grid">
              <div className="stat-card"><h3>Total Users</h3><p className="stat-value">{summary.total_users}</p></div>
              <div className="stat-card"><h3>Students</h3><p className="stat-value">{summary.students}</p></div>
              <div className="stat-card"><h3>Teachers</h3><p className="stat-value">{summary.teachers}</p></div>
              <div className="stat-card"><h3>Classes</h3><p className="stat-value">{summary.classes}</p></div>
              <div className="stat-card"><h3>Active</h3><p className="stat-value">{summary.active_classes}</p></div>
              <div className="stat-card"><h3>Upcoming</h3><p className="stat-value">{summary.upcoming_classes}</p></div>
              <div className="stat-card"><h3>Completed</h3><p className="stat-value">{summary.completed_classes}</p></div>
            </div>
          ) : (
            <p>Loading admin summary...</p>
          )}
        </section>
      </div>
    </div>
  );
};

export default AdminDashboard;
