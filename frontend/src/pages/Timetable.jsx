import React, { useEffect, useState } from 'react'
import { endpoints } from '../api'

const dayOrder = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

const Timetable = () => {
  const [batches, setBatches] = useState([])
  const [selectedBatch, setSelectedBatch] = useState('')
  const [weekly, setWeekly] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    endpoints.batches().then(res => setBatches(res.data)).catch(() => {})
  }, [])

  const loadWeekly = async () => {
    if (!selectedBatch) return
    setLoading(true)
    setError('')
    try {
      const { data } = await endpoints.weeklyByBatch(selectedBatch)
      setWeekly(data.weekly_schedule)
    } catch (e) {
      setError('Failed to load timetable')
    } finally {
      setLoading(false)
    }
  }

  const downloadIcs = () => {
    if (!selectedBatch) return
    const url = endpoints.exportIcsForBatch(selectedBatch)
    window.location.href = url
  }

  return (
    <div className="page">
      <h1>Timetable</h1>
      <div className="controls">
        <select value={selectedBatch} onChange={(e) => setSelectedBatch(e.target.value)}>
          <option value="">Select Batch</option>
          {batches.map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
        <button onClick={loadWeekly} disabled={!selectedBatch || loading}>Load</button>
        <button onClick={downloadIcs} disabled={!selectedBatch}>Export ICS</button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading && <div>Loading...</div>}
      {weekly && (
        <div className="weekly-grid">
          {dayOrder.map(day => (
            <div key={day} className="day-column">
              <h3 style={{ textTransform: 'capitalize' }}>{day}</h3>
              {(weekly[day] || []).map(slot => (
                <div key={slot.id} className="slot-card">
                  <div><strong>{slot.subject}</strong> ({slot.component_type})</div>
                  <div>{slot.start_time} - {slot.end_time}</div>
                  <div>Room: {slot.room || '-'}</div>
                  {slot.staff && <div>Staff: {slot.staff}</div>}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Timetable


