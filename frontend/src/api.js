import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Attach Authorization header from localStorage if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  // Send CSRF token if present (for session-based endpoints if any)
  const csrf = localStorage.getItem('csrftoken')
  if (csrf) {
    config.headers['X-CSRFToken'] = csrf
  }
  return config
})

export const endpoints = {
  health: () => api.get('/health/'),
  batches: () => api.get('/batches/'),
  staffUsers: () => api.get('/users/?role=staff'),
  weeklyByBatch: (batchId) => api.get(`/advanced-timetables/weekly-batch/?batch_id=${batchId}`),
  weeklyByStaff: (staffId) => api.get(`/advanced-timetables/weekly-staff/?staff_id=${staffId}`),
  exportIcsForBatch: (batchId) => `${apiBaseUrl}/advanced-timetables/export-ics/?batch_id=${batchId}`,
  conflicts: (batchId) => api.get(`/scheduling/conflicts/?batch_id=${batchId}`),
  autoResolveConflicts: (batchId) => api.post('/scheduling/conflicts/', { batch_id: batchId, auto_resolve: true }),
  commentsByTimetable: (timetableId) => api.get(`/comments/by_timetable/?timetable_id=${timetableId}`),
  createComment: (payload) => api.post('/comments/', payload),
  profileGet: () => api.get('/auth/profile/'),
  profileUpdate: (payload) => api.put('/auth/profile/', payload),
  logout: (refreshToken) => api.post('/auth/logout/', { refresh_token: refreshToken })
}


