import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

export const verifyVoice = (formData) => api.post('/voice/verify', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getHistory = (userId) => api.get('/history', { params: { user_id: userId } })
export const login = (email, password) => api.post('/auth/login', null, { params: { email, password } })

export default api
