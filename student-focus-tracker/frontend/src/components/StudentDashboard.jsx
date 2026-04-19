import React, { useState, useEffect } from 'react';
import api from '../api';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import './Dashboard.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const StudentDashboard = () => {
  const [availableClasses, setAvailableClasses] = useState([]);
  const [myClasses, setMyClasses] = useState([]);
  const [selectedTab, setSelectedTab] = useState('my');
  const [selectedClass, setSelectedClass] = useState(null);
  const [history, setHistory] = useState([]);
  const [statusMessage, setStatusMessage] = useState('');
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  useEffect(() => {
    fetchClasses();
    fetchAvailableClasses();
  }, []);

  const fetchClasses = async () => {
    const token = localStorage.getItem('token');
    const response = await api.get('/classes', { headers: { Authorization: token } });
    setMyClasses(response.data);
  };

  const fetchAvailableClasses = async () => {
    const token = localStorage.getItem('token');
    const response = await api.get('/classes/available', { headers: { Authorization: token } });
    setAvailableClasses(response.data);
  };

  const fetchHistory = async (classId) => {
    const token = localStorage.getItem('token');
    const response = await api.get(`/history/${classId}`, { headers: { Authorization: token } });
    setHistory(response.data.history.reverse());
  };

  const handleClassSelect = (cls) => {
    setSelectedClass(cls);
    setSelectedTab('my');
    fetchHistory(cls._id);
  };

  const joinClass = async (classId) => {
    try {
      const token = localStorage.getItem('token');
      await api.post(`/classes/${classId}/join`, {}, { headers: { Authorization: token } });
      setStatusMessage('Joined class successfully. Focus tracking is ready to start.');
      fetchClasses();
      fetchAvailableClasses();
    } catch (error) {
      setStatusMessage(error.response?.data?.error || 'Failed to join class');
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
      title: { display: true, text: selectedClass ? `${selectedClass.class_name} Focus History` : '' },
    },
    scales: {
      y: { beginAtZero: true, max: 10 },
    },
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header student-header">
        <h1>🎓 Student Dashboard</h1>
        <p>Welcome, {user?.name}!</p>
        <button className="logout-btn" onClick={() => { localStorage.clear(); window.location.href = '/'; }}>Logout</button>
      </header>

      <div className="dashboard-content">
        <section className="tabs-row">
          <button className={`tab-button ${selectedTab === 'available' ? 'active' : ''}`} onClick={() => setSelectedTab('available')}>Available</button>
          <button className={`tab-button ${selectedTab === 'my' ? 'active' : ''}`} onClick={() => setSelectedTab('my')}>My Classes</button>
          <button className={`tab-button ${selectedTab === 'upcoming' ? 'active' : ''}`} onClick={() => setSelectedTab('upcoming')}>Upcoming</button>
          <button className={`tab-button ${selectedTab === 'completed' ? 'active' : ''}`} onClick={() => setSelectedTab('completed')}>Completed</button>
        </section>

        {statusMessage && <div className="status-banner">{statusMessage}</div>}

        {selectedTab === 'available' && (
          <section className="classes-section">
            <h2>📚 Available Classes</h2>
            <div className="classes-grid">
              {availableClasses.length === 0 ? (
                <div className="empty-card">No classes are available right now.</div>
              ) : availableClasses.map((cls) => (
                <div key={cls._id} className="class-card">
                  <h3>{cls.class_name}</h3>
                  <p>Teacher: {cls.teacher_email}</p>
                  <p>Status: {cls.status}</p>
                  <p>Starts: {new Date(cls.start_time).toLocaleString()}</p>
                  <button className="action-btn" onClick={() => joinClass(cls._id)}>Join Class</button>
                </div>
              ))}
            </div>
          </section>
        )}

        {selectedTab === 'my' && (
          <section className="classes-section">
            <h2>📚 My Classes</h2>
            <div className="classes-grid">
              {myClasses.length === 0 ? (
                <div className="empty-card">No classes found. Join a class to start tracking.</div>
              ) : myClasses.map((cls) => (
                <div key={cls._id} className="class-card" onClick={() => handleClassSelect(cls)}>
                  <h3>{cls.class_name}</h3>
                  <p>Teacher: {cls.teacher_email}</p>
                  <p>Status: {cls.status}</p>
                  <p>{new Date(cls.start_time).toLocaleString()}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {selectedTab === 'upcoming' && (
          <section className="classes-section">
            <h2>🕒 Upcoming Classes</h2>
            <div className="classes-grid">
              {myClasses.filter((cls) => cls.status === 'upcoming').length === 0 ? (
                <div className="empty-card">No upcoming classes.</div>
              ) : myClasses.filter((cls) => cls.status === 'upcoming').map((cls) => (
                <div key={cls._id} className="class-card" onClick={() => handleClassSelect(cls)}>
                  <h3>{cls.class_name}</h3>
                  <p>Starts: {new Date(cls.start_time).toLocaleString()}</p>
                  <p>Teacher: {cls.teacher_email}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {selectedTab === 'completed' && (
          <section className="classes-section">
            <h2>✅ Completed Classes</h2>
            <div className="classes-grid">
              {myClasses.filter((cls) => cls.status === 'completed').length === 0 ? (
                <div className="empty-card">No completed classes yet.</div>
              ) : myClasses.filter((cls) => cls.status === 'completed').map((cls) => (
                <div key={cls._id} className="class-card" onClick={() => handleClassSelect(cls)}>
                  <h3>{cls.class_name}</h3>
                  <p>Ended: {new Date(cls.end_time).toLocaleString()}</p>
                  <p>Teacher: {cls.teacher_email}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {selectedClass && history.length > 0 && (
          <section className="chart-section">
            <h2>📊 {selectedClass.class_name} Focus History</h2>
            <div className="chart-container">
              <Line data={chartData} options={chartOptions} />
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;
