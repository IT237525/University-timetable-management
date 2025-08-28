import React, { useState, useEffect } from 'react'
import './Students.css'

const Students = () => {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setStudents([
        { id: 1, name: 'John Doe', email: 'john@northern.edu', major: 'Computer Science', year: 'Junior' },
        { id: 2, name: 'Jane Smith', email: 'jane@northern.edu', major: 'Mathematics', year: 'Senior' },
        { id: 3, name: 'Mike Johnson', email: 'mike@northern.edu', major: 'Physics', year: 'Sophomore' },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return <div className="loading">Loading students...</div>
  }

  return (
    <div className="students">
      <h1>Students</h1>
      <div className="students-grid">
        {students.map(student => (
          <div key={student.id} className="student-card">
            <h3>{student.name}</h3>
            <p><strong>Email:</strong> {student.email}</p>
            <p><strong>Major:</strong> {student.major}</p>
            <p><strong>Year:</strong> {student.year}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Students
