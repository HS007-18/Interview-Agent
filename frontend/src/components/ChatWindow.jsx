import React, { useState, useEffect, useRef } from 'react';

export default function ChatWindow({ sessionId, candidate, onComplete }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    const startInterview = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/interview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionId, candidate })
        });
        const data = await res.json();
        setMessages([{ role: 'interviewer', text: data.reply }]);
        if (data.done) {
          setTimeout(() => onComplete(data.feedback), 2000);
        }
      } catch (err) {
        console.error(err);
        setMessages([{ role: 'system', text: 'Error starting interview session.' }]);
      }
      setLoading(false);
    };
    startInterview();
  }, [sessionId, candidate]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'candidate', text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('/api/interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: userMsg })
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'interviewer', text: data.reply }]);
      
      if (data.done) {
        setTimeout(() => {
          onComplete(data.feedback);
        }, 2000);
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'system', text: 'Error transmitting response to AI interviewer.' }]);
    }
    setLoading(false);
  };

  const getInitials = (name = '') => {
    return name
      .split(' ')
      .map(p => p[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'C';
  };

  const candidateName = candidate?.member?.name || 'Candidate';
  const shortSessionId = sessionId ? `${sessionId.slice(0, 8)}...` : 'Active';

  return (
    <div className="chat-window">
      <div className="chat-header-banner">
        <div className="chat-candidate-profile">
          <div className="candidate-avatar-sm">
            {getInitials(candidateName)}
          </div>
          <div className="chat-candidate-info">
            <h3>{candidateName}</h3>
            <p>{candidate?.member?.jobRole} • {candidate?.member?.yearsExperience || 0} YOE</p>
          </div>
        </div>

        <div className="session-indicator">
          <span className="live-dot"></span>
          <span>SESSION: {shortSessionId}</span>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'interviewer' && (
              <div className="msg-avatar" title="AI Technical Interviewer">
                AI
              </div>
            )}
            {msg.role === 'candidate' && (
              <div className="msg-avatar" title={candidateName}>
                {getInitials(candidateName)}
              </div>
            )}
            
            <div className="message-body">
              {msg.role !== 'system' && (
                <span className="sender-label">
                  {msg.role === 'interviewer' ? 'AI Interviewer' : candidateName}
                </span>
              )}
              <div className="message-bubble">
                {msg.text}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-wrapper interviewer">
            <div className="msg-avatar">AI</div>
            <div className="message-body">
              <span className="sender-label">AI Interviewer</span>
              <div className="message-bubble typing-container">
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Evaluating response</span>
                <div className="typing-dots">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={sendMessage}>
        <div className="input-container">
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type technical response..."
            disabled={loading}
            autoFocus
          />
          <span className="input-hint">Press Enter ↵</span>
        </div>
        <button type="submit" disabled={loading || !input.trim()}>
          <span>Send</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
