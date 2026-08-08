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
    // Start interview
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
        setMessages([{ role: 'system', text: 'Error starting interview.' }]);
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
      setMessages(prev => [...prev, { role: 'system', text: 'Error sending message.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="candidate-info">
          <h3>Interviewing: {candidate.member?.name}</h3>
          <p>{candidate.member?.jobRole}</p>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message-wrapper ${msg.role}`}>
            <div className="message-bubble">
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message-wrapper interviewer">
            <div className="message-bubble typing">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={sendMessage}>
        <input 
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your response..."
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
