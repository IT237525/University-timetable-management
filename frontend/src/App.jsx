import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { RequireAuth, RequireGuest } from './auth'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Students from './pages/Students'
import Courses from './pages/Courses'
import Departments from './pages/Departments'
import Login from './pages/Login'
import Register from './pages/Register'
import Timetable from './pages/Timetable'
import Conflicts from './pages/Conflicts'
import Comments from './pages/Comments'
import Profile from './pages/Profile'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/students" element={<Students />} />
            <Route path="/courses" element={<Courses />} />
            <Route path="/departments" element={<Departments />} />
            <Route path="/login" element={<RequireGuest><Login /></RequireGuest>} />
            <Route path="/register" element={<RequireGuest><Register /></RequireGuest>} />
            <Route path="/timetable" element={<Timetable />} />
            <Route path="/conflicts" element={<Conflicts />} />
            <Route path="/comments" element={<Comments />} />
            <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
