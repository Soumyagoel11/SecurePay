import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../services/api'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const res = await api.get('/auth/me')
      setUser(res.data.data.user)
      setProfile(res.data.data.profile)
    } catch (e) {
      localStorage.removeItem('token')
      setUser(null)
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    localStorage.setItem('token', res.data.data.access_token)
    setUser(res.data.data.user)
    // fetch profile after login
    const me = await api.get('/auth/me')
    setProfile(me.data.data.profile)
    return res.data.data.user
  }

  const register = async (payload) => {
    const res = await api.post('/auth/register', payload)
    localStorage.setItem('token', res.data.data.access_token)
    setUser(res.data.data.user)
    const me = await api.get('/auth/me')
    setProfile(me.data.data.profile)
    return res.data.data.user
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setProfile(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, profile, loading, login, register, logout, fetchMe, setUser, setProfile }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
