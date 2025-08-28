import React, { useState } from 'react'
import { endpoints } from '../api'

const Comments = () => {
  const [timetableId, setTimetableId] = useState('')
  const [comments, setComments] = useState([])
  const [text, setText] = useState('')
  const [userId, setUserId] = useState('')
  const [message, setMessage] = useState('')

  const load = async () => {
    if (!timetableId) return
    try {
      const { data } = await endpoints.commentsByTimetable(timetableId)
      setComments(data)
    } catch (e) {
      setMessage('Failed to load comments')
    }
  }

  const submit = async () => {
    if (!timetableId || !userId || !text) return
    try {
      await endpoints.createComment({ user: Number(userId), timetable: Number(timetableId), text })
      setText('')
      setMessage('Comment submitted for approval')
      await load()
    } catch (e) {
      setMessage('Failed to submit comment')
    }
  }

  return (
    <div className="page">
      <h1>Comments</h1>
      <div className="controls">
        <input placeholder="Timetable ID" value={timetableId} onChange={(e) => setTimetableId(e.target.value)} />
        <button onClick={load} disabled={!timetableId}>Load</button>
      </div>
      <div className="new-comment">
        <input placeholder="Your User ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
        <textarea placeholder="Write a comment..." value={text} onChange={(e) => setText(e.target.value)} />
        <button onClick={submit} disabled={!timetableId || !userId || !text}>Submit</button>
      </div>
      {message && <div className="info">{message}</div>}
      <div className="comment-list">
        {comments.map(c => (
          <div key={c.id} className="comment-item">
            <div><strong>{c.user_name}</strong></div>
            <div>{c.text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Comments


