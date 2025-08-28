import React, { useState, useEffect } from 'react'
import './Courses.css'

const Courses = () => {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setCourses([
        { id: 1, name: 'Introduction to Computer Science', code: 'CS101', credits: 3, instructor: 'Dr. Smith' },
        { id: 2, name: 'Calculus I', code: 'MATH201', credits: 4, instructor: 'Dr. Johnson' },
        { id: 3, name: 'Physics Fundamentals', code: 'PHYS101', credits: 4, instructor: 'Dr. Williams' },
        { id: 4, name: 'Data Structures', code: 'CS201', credits: 3, instructor: 'Dr. Brown' },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return <div className="loading">Loading courses...</div>
  }

  return (
    <div className="courses">
      <h1>Courses</h1>
      <div className="courses-grid">
        {courses.map(course => (
          <div key={course.id} className="course-card">
            <h3>{course.name}</h3>
            <p><strong>Code:</strong> {course.code}</p>
            <p><strong>Credits:</strong> {course.credits}</p>
            <p><strong>Instructor:</strong> {course.instructor}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Courses
