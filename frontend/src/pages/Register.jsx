import React, { useState } from 'react'
import { api } from '../api'
import { Container, Box, TextField, Button, Typography, Card, CardContent, MenuItem, Link as MLink } from '@mui/material'

const Register = () => {
  const [form, setForm] = useState({ username: '', email: '', first_name: '', last_name: '', role: 'student', phone: '', password: '', confirm_password: '' })
  const [error, setError] = useState('')

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/register/', form)
      localStorage.setItem('access', data.tokens.access)
      localStorage.setItem('refresh', data.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(data.user))
      window.location.href = '/'
    } catch (e) {
      const detail = e?.response?.data?.error || e?.response?.data?.detail || 'Registration failed'
      setError(typeof detail === 'string' ? detail : 'Registration failed')
    }
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Card elevation={4}>
        <CardContent>
          <Typography variant="h4" component="h1" gutterBottom>Register</Typography>
          <Box component="form" onSubmit={onSubmit} sx={{ display: 'grid', gap: 2 }}>
            <TextField name="username" label="Username" value={form.username} onChange={onChange} required fullWidth />
            <TextField name="email" label="Email" type="email" value={form.email} onChange={onChange} required fullWidth />
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <TextField name="first_name" label="First name" value={form.first_name} onChange={onChange} fullWidth />
              <TextField name="last_name" label="Last name" value={form.last_name} onChange={onChange} fullWidth />
            </Box>
            <TextField name="role" label="Role" select value={form.role} onChange={onChange} fullWidth>
              <MenuItem value="student">Student</MenuItem>
              <MenuItem value="staff">Staff</MenuItem>
            </TextField>
            <TextField name="phone" label="Phone" value={form.phone} onChange={onChange} fullWidth />
            <TextField name="password" label="Password" type="password" value={form.password} onChange={onChange} required fullWidth />
            <TextField name="confirm_password" label="Confirm password" type="password" value={form.confirm_password} onChange={onChange} required fullWidth />
            {error && <Typography color="error" variant="body2">{error}</Typography>}
            <Button type="submit" variant="contained" size="large">Create account</Button>
          </Box>
          <Box sx={{ mt: 2 }}>
            <MLink href="/login" underline="hover">Have an account? Login</MLink>
          </Box>
        </CardContent>
      </Card>
    </Container>
  )
}

export default Register


