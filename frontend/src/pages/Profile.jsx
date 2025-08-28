import React, { useEffect, useState } from 'react'
import { endpoints } from '../api'
import { Container, Box, TextField, Button, Typography, Card, CardContent } from '@mui/material'

const Profile = () => {
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', email: '' })
  const [message, setMessage] = useState('')

  const load = async () => {
    try {
      const { data } = await endpoints.profileGet()
      setProfile(data)
      setForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        phone: data.phone || '',
        email: data.email || ''
      })
    } catch (e) {
      setMessage('Failed to load profile')
    }
  }

  useEffect(() => { load() }, [])

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSave = async (e) => {
    e.preventDefault()
    setMessage('')
    try {
      await endpoints.profileUpdate(form)
      setMessage('Profile updated')
      await load()
    } catch (e) {
      setMessage('Update failed')
    }
  }

  const onLogout = async () => {
    try {
      const refresh = localStorage.getItem('refresh')
      await endpoints.logout(refresh)
    } catch {}
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  if (!profile) return <Container sx={{ mt: 8 }}>Loading...</Container>

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Card elevation={4}>
        <CardContent>
          <Typography variant="h4" component="h1" gutterBottom>My Profile</Typography>
          <Box component="form" onSubmit={onSave} sx={{ display: 'grid', gap: 2 }}>
            <TextField name="first_name" label="First name" value={form.first_name} onChange={onChange} fullWidth />
            <TextField name="last_name" label="Last name" value={form.last_name} onChange={onChange} fullWidth />
            <TextField name="phone" label="Phone" value={form.phone} onChange={onChange} fullWidth />
            <TextField name="email" label="Email" value={form.email} onChange={onChange} fullWidth />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button type="submit" variant="contained">Save</Button>
              <Button type="button" color="secondary" onClick={onLogout}>Logout</Button>
            </Box>
          </Box>
          {message && <Typography sx={{ mt: 2 }}>{message}</Typography>}
        </CardContent>
      </Card>
    </Container>
  )
}

export default Profile


