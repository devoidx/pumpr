import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'

const BASE = '/api/v1/auth'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(null)
  const [accessToken, setAccessToken] = useState(null)
  const [loading, setLoading]         = useState(true)
  const refreshTimer                  = useRef(null)

  function scheduleRefresh(expiresIn) {
    if (refreshTimer.current) clearTimeout(refreshTimer.current)
    const delay = Math.max((expiresIn - 60) * 1000, 10_000)
    refreshTimer.current = setTimeout(doSilentRefresh, delay)
  }

  function clearAuth() {
    setAccessToken(null)
    setUser(null)
    if (refreshTimer.current) clearTimeout(refreshTimer.current)
  }

  async function doSilentRefresh() {
    try {
      const res = await fetch(`${BASE}/refresh`, { method: 'POST', credentials: 'include' })
      if (!res.ok) { clearAuth(); return null }
      const { access_token, expires_in } = await res.json()
      const meRes = await fetch(`${BASE}/me`, { headers: { Authorization: `Bearer ${access_token}` } })
      if (!meRes.ok) { clearAuth(); return null }
      const userObj = await meRes.json()
      setAccessToken(access_token)
      setUser(userObj)
      scheduleRefresh(expires_in)
      return access_token
    } catch {
      clearAuth()
      return null
    }
  }

  useEffect(() => {
    doSilentRefresh().finally(() => setLoading(false))
    return () => { if (refreshTimer.current) clearTimeout(refreshTimer.current) }
  }, [])

  async function login(email, password) {
    const res = await fetch(`${BASE}/login`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({}))
      throw new Error(e.detail || 'Login failed')
    }
    const { access_token, expires_in } = await res.json()
    const meRes = await fetch(`${BASE}/me`, { headers: { Authorization: `Bearer ${access_token}` } })
    if (!meRes.ok) throw new Error('Failed to get user info')
    const userObj = await meRes.json()
    setAccessToken(access_token)
    setUser(userObj)
    scheduleRefresh(expires_in)
    if (typeof umami !== 'undefined') umami.track('user-login', { role: userObj.role })
  }

  async function register(email, username, password) {
    const res = await fetch(`${BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({}))
      throw new Error(e.detail || 'Registration failed')
    }
    return res.json()
  }

  async function logout() {
    await fetch(`${BASE}/logout`, {
      method: 'POST', credentials: 'include',
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    }).catch(() => {})
    if (typeof umami !== 'undefined') umami.track('user-logout')
    clearAuth()
  }

  async function updateProfile(updates) {
    const res = await fetch(`${BASE}/me`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify(updates),
    })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Update failed') }
    const updated = await res.json()
    setUser(updated)
    return updated
  }

  async function requestPasswordReset(email) {
    const res = await fetch(`${BASE}/password-reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    return res.json()
  }

  const authFetch = useCallback(async (url, options = {}) => {
    const headers = {
      ...(options.headers || {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    }
    return fetch(url, { ...options, headers })
  }, [accessToken])

  return (
    <AuthContext.Provider value={{
      user, accessToken, loading,
      isAuthenticated: !!accessToken,
      login, register, logout, requestPasswordReset, updateProfile, authFetch,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
