import React from 'react'
import { Link } from 'react-router-dom'
import { AppBar, Toolbar, Button, Box } from '@mui/material'
import './Navbar.css'

const isLoggedIn = () => Boolean(localStorage.getItem('access'))
const isAdmin = () => {
  try { const u = JSON.parse(localStorage.getItem('user') || 'null'); return u && u.role === 'admin' } catch { return false }
}

const Navbar = () => {
  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ display: 'flex', gap: 1 }}>
        <Button color="inherit" component={Link} to="/">Northern University</Button>
        <Box sx={{ flexGrow: 1 }} />
        {!isLoggedIn() && <Button color="inherit" component={Link} to="/login">Login</Button>}
        {!isLoggedIn() && <Button color="inherit" component={Link} to="/register">Register</Button>}
        {isLoggedIn() && <Button color="inherit" component={Link} to="/profile">Profile</Button>}
        <Button color="inherit" component={Link} to="/">Home</Button>
        <Button color="inherit" component={Link} to="/students">Students</Button>
        <Button color="inherit" component={Link} to="/courses">Courses</Button>
        <Button color="inherit" component={Link} to="/departments">Departments</Button>
        <Button color="inherit" component={Link} to="/timetable">Timetable</Button>
        <Button color="inherit" component={Link} to="/conflicts">Conflicts</Button>
        <Button color="inherit" component={Link} to="/comments">Comments</Button>
        {isAdmin() && <Button color="secondary" variant="outlined" href="http://localhost:8000/admin">Admin</Button>}
      </Toolbar>
    </AppBar>
  )
}

export default Navbar
