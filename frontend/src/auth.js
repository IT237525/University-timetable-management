import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const isAuthenticated = () => {
  const token = localStorage.getItem('access')
  return Boolean(token)
}

export const isAdmin = () => {
  const user = getStoredUser()
  return Boolean(user && user.role === 'admin')
}

export const RequireAuth = ({ children }) => {
  const location = useLocation()
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return children
}

export const RequireGuest = ({ children }) => {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }
  return children
}

export const RequireAdmin = ({ children }) => {
  const location = useLocation()
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (!isAdmin()) {
    return <Navigate to="/" replace />
  }
  return children
}


