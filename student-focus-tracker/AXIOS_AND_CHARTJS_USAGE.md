# Axios & Chart.js Usage in Student Focus Tracker

## 📍 Axios Usage

**Axios** is an HTTP client library used to make API requests from the React frontend to the Flask backend.

### Location: [frontend/src/api.js](frontend/src/api.js)

**Purpose**: Centralized API client configuration

```javascript
import axios from 'axios';

// Create axios instance with base URL and timeout
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add Authorization token to all requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = token;
  }
  return config;
});

// Handle response errors (401 redirects to login)
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/';
  }
  return Promise.reject(error);
});

export default api;
```

### Where Axios is Used:

#### 1. **StudentDashboard.jsx** - Fetching class and focus data
```javascript
import api from '../api';

// Fetch user's classes
const response = await api.get('/classes', { 
  headers: { Authorization: token } 
});

// Fetch available classes to join
const response = await api.get('/classes/available', { 
  headers: { Authorization: token } 
});

// Fetch focus history for a specific class
axios.get('/api/focus-history?limit=60', {
  headers: { 'Authorization': localStorage.getItem('token') }
});
```

#### 2. **TeacherDashboard.jsx** - Getting class statistics
```javascript
// Fetch class-wide statistics
await api.get(`/class-statistics/${classId}`);

// Get student list with focus data
await api.get(`/class/${classId}/students`);
```

#### 3. **Login.jsx** - User authentication
```javascript
// Send login credentials
api.post('/login', { username, password });

// Send registration data
api.post('/register', { username, email, password, role });
```

#### 4. **AdminDashboard.jsx** - System management
```javascript
// Fetch all users
api.get('/users');

// Create new user
api.post('/users', userData);

// Delete user
api.delete(`/users/${userId}`);
```

### API Endpoints Called via Axios:
- **POST** `/register` - User registration
- **POST** `/login` - User login
- **GET** `/classes` - Fetch user's classes
- **GET** `/classes/available` - Available classes to join
- **GET** `/class-statistics/{classId}` - Class analytics
- **GET** `/focus-history` - Historical focus data
- **POST** `/focus-record` - Submit focus tracking data
- **GET** `/student-stats/{studentId}` - Individual student stats

---

## 📊 Chart.js Usage

**Chart.js** (with react-chartjs-2 wrapper) is used for visualizing focus tracking data with interactive charts.

### Location: [frontend/src/components/StudentDashboard.jsx](frontend/src/components/StudentDashboard.jsx)

**Purpose**: Display real-time and historical focus scores in graphical format

```javascript
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, 
         LineElement, Title, Tooltip, Legend } from 'chart.js';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, 
                 Title, Tooltip, Legend);

// Create line chart data
const chartData = {
  labels: history.map(h => new Date(h.timestamp).toLocaleTimeString()),
  datasets: [{
    label: 'Focus Score',
    data: history.map(h => h.focus_score),
    borderColor: 'rgb(75, 192, 192)',
    tension: 0.1,
    fill: false
  }]
};

// Render chart component
<Line data={chartData} options={{ responsive: true }} />
```

### Chart.js Usage Locations:

#### 1. **StudentDashboard.jsx** - Focus trend over time
```javascript
// Display focus score trend (last 60 data points)
const chartData = {
  labels: history.map(h => new Date(h.timestamp).toLocaleTimeString()),
  datasets: [{
    label: 'Focus Score (0-10)',
    data: history.map(h => h.focus_score),
    borderColor: '#0066CC',
    backgroundColor: 'rgba(0, 102, 204, 0.1)',
    tension: 0.1
  }]
};

return (
  <div className="chart-container">
    <Line data={chartData} options={chartOptions} />
  </div>
);
```

**Shows**: 
- Real-time focus score changes
- Trend over selected time period
- Peak and low focus moments
- Horizontal axis: Time
- Vertical axis: Focus Score (0-10)

#### 2. **TeacherDashboard.jsx** - Class-wide analytics
```javascript
// Bar chart comparing student focus scores
const classStatsChart = {
  labels: students.map(s => s.name),
  datasets: [{
    label: 'Average Focus Score',
    data: students.map(s => s.avgFocusScore),
    backgroundColor: ['#00AA66', '#0066CC', '#FF6600'],
  }]
};

<Bar data={classStatsChart} />
```

**Shows**:
- Student comparison by focus performance
- Class average vs individual scores
- Identify high/low performers

#### 3. **Streamlit Dashboard** ([dashboard/app.py](dashboard/app.py)) - Analytics visualizations
```python
# Line chart of focus score over time
st.line_chart(history.set_index("timestamp")["focus_score"])

# Area chart showing focus distribution
st.area_chart(chart_data, color="#00D084")
```

---

## 📈 Complete Data Flow: Axios → Chart.js

```
1. Frontend loads StudentDashboard.jsx
    ↓
2. useEffect() calls fetchData()
    ↓
3. Axios makes GET request via api.js
    axios.get('/focus-history?limit=60')
    ↓
4. Request interceptor adds JWT token
    ↓
5. Request sent to Flask backend
    ↓
6. Backend returns JSON: [
     { timestamp: "2024-05-15T10:30:00Z", focus_score: 8.5 },
     { timestamp: "2024-05-15T10:31:00Z", focus_score: 7.2 },
     ...
    ]
    ↓
7. Response stored in state: setHistory(response.data)
    ↓
8. Chart.js transforms data into chart format
    labels: ["10:30:00", "10:31:00", ...]
    data: [8.5, 7.2, ...]
    ↓
9. Line component renders interactive chart
    ↓
10. User sees real-time focus graph
```

---

## 🔌 Connection Summary

### Axios Responsibilities:
- ✅ Making HTTP requests to backend
- ✅ Adding authentication tokens
- ✅ Handling errors and timeouts
- ✅ Managing request/response interceptors
- ✅ Serializing/deserializing JSON data

### Chart.js Responsibilities:
- ✅ Creating interactive charts
- ✅ Visualizing numerical data
- ✅ Providing zooming/panning capabilities
- ✅ Tooltip and legend display
- ✅ Responsive chart resizing

### How They Work Together:
```
Axios fetches data from API
        ↓
Data stored in React state
        ↓
Chart.js consumes data from state
        ↓
Chart rendered to browser
        ↓
User sees interactive visualization
```

---

## 📦 Package Configuration

### In [frontend/package.json](frontend/package.json):

```json
{
  "dependencies": {
    "axios": "^1.15.0",
    "chart.js": "^4.5.1",
    "react-chartjs-2": "^5.3.1",
    "react": "^19.2.5",
    "react-dom": "^19.2.5"
  }
}
```

---

## 🎯 Key Features

### Axios Features Used:
- **Interceptors**: Automatically add auth tokens
- **Timeout**: 30-second limit for requests
- **Error Handling**: Redirects to login on 401 errors
- **Base URL**: Centralizes API endpoint configuration

### Chart.js Features Used:
- **Line Charts**: Focus score trends over time
- **Bar Charts**: Student comparisons
- **Area Charts**: Aggregated data visualization
- **Responsive Design**: Auto-scales with container
- **Legend & Tooltips**: Interactive data exploration

