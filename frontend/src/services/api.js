import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request automatically.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Normalize error responses.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const data = error.response && error.response.data
    const message =
      (data && data.message) || error.message || 'Request failed'
    return Promise.reject({ status: error.response && error.response.status, message })
  }
)

export default api
export { API_URL }
