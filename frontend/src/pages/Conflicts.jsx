import React, { useState } from 'react'
import { endpoints } from '../api'

const Conflicts = () => {
  const [batchId, setBatchId] = useState('')
  const [conflicts, setConflicts] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const loadConflicts = async () => {
    if (!batchId) return
    setLoading(true)
    setMessage('')
    try {
      const { data } = await endpoints.conflicts(batchId)
      setConflicts(data.conflicts || [])
    } catch (e) {
      setMessage('Failed to load conflicts')
    } finally {
      setLoading(false)
    }
  }

  const autoResolve = async () => {
    if (!batchId) return
    setLoading(true)
    setMessage('')
    try {
      const { data } = await endpoints.autoResolveConflicts(batchId)
      setMessage(data.message || 'Auto resolve complete')
      await loadConflicts()
    } catch (e) {
      setMessage('Failed to auto-resolve conflicts')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1>Conflicts</h1>
      <div className="controls">
        <input placeholder="Batch ID" value={batchId} onChange={(e) => setBatchId(e.target.value)} />
        <button onClick={loadConflicts} disabled={!batchId || loading}>Load</button>
        <button onClick={autoResolve} disabled={!batchId || loading}>Auto Resolve</button>
      </div>
      {message && <div className="info">{message}</div>}
      {loading && <div>Loading...</div>}
      <div className="conflict-list">
        {conflicts.map((c, idx) => (
          <div key={idx} className="conflict-item">
            <div><strong>Type:</strong> {c.type}</div>
            <div>{c.message}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Conflicts


