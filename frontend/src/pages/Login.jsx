import React, { useState } from 'react'
import { api } from '../api'
import { Container, Box, TextField, Button, Typography, Card, CardContent, Link as MLink } from '@mui/material'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/login/', { username, password })
      localStorage.setItem('access', data.tokens.access)
      localStorage.setItem('refresh', data.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(data.user))
      if (data.user && data.user.role === 'admin') {
        window.location.href = 'http://localhost:8000/admin'
      } else {
        window.location.href = '/'
      }
    } catch (e) {
      setError('Invalid credentials')
    }
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Card elevation={4}>
        <CardContent>
          <Typography variant="h4" component="h1" gutterBottom>Login</Typography>
          <Box component="form" onSubmit={onSubmit} sx={{ display: 'grid', gap: 2 }}>
            <TextField label="Username" value={username} onChange={(e) => setUsername(e.target.value)} required fullWidth />
            <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required fullWidth />
            {error && <Typography color="error" variant="body2">{error}</Typography>}
            <Button type="submit" variant="contained" size="large">Login</Button>
          </Box>
          <Box sx={{ mt: 2 }}>
            <MLink href="/register" underline="hover">Create an account</MLink>
          </Box>
        </CardContent>
      </Card>
    </Container>
  )
}

export default Login


