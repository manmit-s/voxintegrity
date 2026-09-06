import axios from 'axios'
import supabase from './supabaseClient'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = supabase
    ? await supabase.auth.getSession()
    : { data: { session: null } }
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

export const verifyVoice = (formData) => api.post('/voice/verify', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getHistory = () => api.get('/history')
export const login = (email, password) => api.post('/auth/login', { email, password })

export default api
