import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
  const [trackingStatus, setTrackingStatus] = useState({}); // Track which classes have tracking started
  const [statusMessage, setStatusMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  useEffect(() => {
    if (!user) {
      window.location.href = '/';
      return;
    }
    fetchData();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const joinId = params.get('join');
    if (joinId) {
      joinClass(joinId);
    }
  }, [location.search]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      await Promise.all([fetchClasses(), fetchAvailableClasses()]);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchClasses = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return;
      }
      const response = await api.get('/classes', { headers: { Authorization: token } });
      setMyClasses(response.data);
    } catch (error) {
      console.error('Failed to fetch classes:', error);
      setMyClasses([]);
    }
  };

  const fetchAvailableClasses = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return;
      }
      const response = await api.get('/classes/available', { headers: { Authorization: token } });
      setAvailableClasses(response.data);
    } catch (error) {
      console.error('Failed to fetch available classes:', error);
      setAvailableClasses([]);
    }
  };

  const fetchHistory = async (classId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const response = await api.get(`/history/${classId}`, { headers: { Authorization: token } });
      setHistory(response.data.history.reverse());
    } catch (error) {
      console.error('Failed to fetch history:', error);
      setHistory([]);
    }
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
      setStatusMessage('✅ Joined class successfully! Click "Start Tracking" below to begin focus monitoring.');
      fetchClasses();
      fetchAvailableClasses();
    } catch (error) {
      setStatusMessage(error.response?.data?.error || 'Failed to join class');
    }
  };

  const startTracking = async (cls) => {
    try {
      setTrackingStatus(prev => ({ ...prev, [cls._id]: true }));
      setStatusMessage('🎥 Starting camera tracking...');
      
      const token = localStorage.getItem('token');
      const response = await api.post(`/start-tracking/${cls._id}`, {}, { 
        headers: { Authorization: token } 
      });

      if (response.status === 200) {
        setStatusMessage('✅ Tracking started! Opening meeting link...');
        if (cls.meeting_url) {
          window.open(cls.meeting_url, '_blank', 'noopener,noreferrer');
          setTimeout(() => {
            setStatusMessage('✅ Meeting opened & camera tracking active! Press "Stop Tracking" when done.');
          }, 1000);
        } else {
          setStatusMessage('✅ Tracking started successfully! Your focus is being monitored.');
        }
      }
    } catch (error) {
      setTrackingStatus(prev => ({ ...prev, [cls._id]: false }));
      const errorMsg = error.response?.data?.error || error.message || 'Failed to start tracking';
      setStatusMessage(`❌ ${errorMsg}`);
    }
  };

  const stopTracking = async (cls) => {
    try {
      setStatusMessage('⏹ Stopping tracking...');
      const token = localStorage.getItem('token');
      
      await api.post(`/stop-tracking/${cls._id}`, {}, { 
        headers: { Authorization: token } 
      });
      
      setTrackingStatus(prev => ({ ...prev, [cls._id]: false }));
      setStatusMessage('✅ Tracking stopped. Your focus data has been saved.');
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to stop tracking';
      setStatusMessage(`⚠ ${errorMsg}`);
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
        {loading && (
          <div className="loading-state">
            <h2>Loading dashboard...</h2>
          </div>
        )}

        {error && (
          <div className="error-state">
            <h2>Error: {error}</h2>
            <button onClick={fetchData}>Retry</button>
          </div>
        )}

        {!loading && !error && (
          <>
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
                  <p>Status: <span className={`status-${cls.status}`}>{cls.status}</span></p>
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
                  <p>Status: <span className={`status-${cls.status}`}>{cls.status}</span></p>
                  <p>{new Date(cls.start_time).toLocaleString()}</p>
                  {cls.status === 'active' && (
                    <div>
                      {trackingStatus[cls._id] ? (
                        <div className="tracking-controls">
                          <div className="tracking-active">
                            🎥 Camera Tracking Active
                          </div>
                          <button
                            type="button"
                            className="action-btn stop-tracking-btn"
                            onClick={(e) => { e.stopPropagation(); stopTracking(cls); }}
                          >
                            ⏹ Stop Tracking
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="action-btn tracking-btn"
                          onClick={(e) => { e.stopPropagation(); startTracking(cls); }}
                        >
                          🎥 Start Tracking
                        </button>
                      )}
                    </div>
                  )}
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
          </>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;
