import React, { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';
import './Register.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'student',
    student_id: '',
    secret_code: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      // Validation
      if (!formData.name.trim()) {
        setError('Name is required');
        setLoading(false);
        return;
      }
      if (!formData.email.trim()) {
        setError('Email is required');
        setLoading(false);
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setError('Please enter a valid email');
        setLoading(false);
        return;
      }
      if (!formData.password || formData.password.length < 6) {
        setError('Password must be at least 6 characters');
        setLoading(false);
        return;
      }
      if ((formData.role === 'teacher' || formData.role === 'admin') && !formData.secret_code.trim()) {
        setError(`${formData.role.charAt(0).toUpperCase() + formData.role.slice(1)} registration code is required`);
        setLoading(false);
        return;
      }

      const response = await api.post('/register', formData);
      alert('Registration successful! Please login.');
      navigate('/');
    } catch (e) {
      const errorMsg = e.response?.data?.error || e.message || 'Registration failed';
      setError(errorMsg);
      console.error('Register error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h2 className="register-title">Create Account</h2>
        <p className="register-subtitle">Register as student, teacher, or admin</p>
        <form onSubmit={handleRegister} className="register-form">
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              name="name"
              placeholder="Enter your full name"
              value={formData.name}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              placeholder="Create a password"
              value={formData.password}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label>Role</label>
            <select name="role" value={formData.role} onChange={handleChange} className="form-select">
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {formData.role === 'student' && (
            <div className="form-group">
              <label>Student ID</label>
              <input
                type="text"
                name="student_id"
                placeholder="Optional student id"
                value={formData.student_id}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          )}
          {(formData.role === 'teacher' || formData.role === 'admin') && (
            <div className="form-group">
              <label>{formData.role === 'teacher' ? 'Teacher Registration Code' : 'Admin Registration Code'}</label>
              <input
                type="password"
                name="secret_code"
                placeholder="Enter registration code"
                value={formData.secret_code}
                onChange={handleChange}
                required
                className="form-input"
              />
            </div>
          )}
          {error && <p className="form-error">{error}</p>}
          <button type="submit" className="register-btn" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        <p className="login-link">
          Already have an account? <span onClick={() => navigate('/')} className="link">Login here</span>
        </p>
      </div>
    </div>
  );
};

export default Register;
