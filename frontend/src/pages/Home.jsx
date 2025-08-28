import React from 'react'
import './Home.css'

const Home = () => {
  return (
    <div className="home">
      <div className="hero-section">
        <h1>Welcome to Northern University</h1>
        <p>Empowering minds, shaping futures</p>
      </div>
      
      <div className="features-grid">
        <div className="feature-card">
          <h3>Academic Excellence</h3>
          <p>World-class education with experienced faculty and modern facilities.</p>
        </div>
        
        <div className="feature-card">
          <h3>Research Innovation</h3>
          <p>Cutting-edge research opportunities across various disciplines.</p>
        </div>
        
        <div className="feature-card">
          <h3>Student Life</h3>
          <p>Rich campus life with diverse activities and organizations.</p>
        </div>
        
        <div className="feature-card">
          <h3>Career Support</h3>
          <p>Comprehensive career services and industry connections.</p>
        </div>
      </div>
    </div>
  )
}

export default Home
