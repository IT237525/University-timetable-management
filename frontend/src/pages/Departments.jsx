import React, { useState, useEffect } from 'react'
import './Departments.css'

const Departments = () => {
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setDepartments([
        { id: 1, name: 'Computer Science', chair: 'Dr. Anderson', faculty: 15, students: 120 },
        { id: 2, name: 'Mathematics', chair: 'Dr. Wilson', faculty: 12, students: 85 },
        { id: 3, name: 'Physics', chair: 'Dr. Davis', faculty: 10, students: 65 },
        { id: 4, name: 'Engineering', chair: 'Dr. Miller', faculty: 18, students: 150 },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return <div className="loading">Loading departments...</div>
  }

  return (
    <div className="departments">
      <h1>Departments</h1>
      <div className="departments-grid">
        {departments.map(department => (
          <div key={department.id} className="department-card">
            <h3>{department.name}</h3>
            <p><strong>Chair:</strong> {department.chair}</p>
            <p><strong>Faculty:</strong> {department.faculty}</p>
            <p><strong>Students:</strong> {department.students}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Departments
