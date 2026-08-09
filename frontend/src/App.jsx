import React, { useState } from 'react';
import CandidateSelect from './components/CandidateSelect';
import ChatWindow from './components/ChatWindow';
import FeedbackPanel from './components/FeedbackPanel';
import './App.css';

function App() {
  const [candidate, setCandidate] = useState(null);
  const [sessionId, setSessionId] = useState('');
  const [feedback, setFeedback] = useState(null);

  const handleSelectCandidate = (selected) => {
    setCandidate(selected);
    setSessionId(crypto.randomUUID());
    setFeedback(null);
  };

  const handleComplete = (finalFeedback) => {
    setFeedback(finalFeedback);
  };

  const handleReset = () => {
    setCandidate(null);
    setSessionId('');
    setFeedback(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              <line x1="9" y1="9" x2="15" y2="9"></line>
              <line x1="9" y1="13" x2="13" y2="13"></line>
            </svg>
          </div>
          <h1>AI Technical Interviewer</h1>
          <span className="header-badge">Hackathon Edition</span>
        </div>

        <div className="header-actions">
          {candidate && (
            <button className="header-reset" onClick={handleReset}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
              Back to Candidates
            </button>
          )}
        </div>
      </header>
      
      <main className="app-main">
        {!candidate && !feedback && (
          <CandidateSelect onSelect={handleSelectCandidate} />
        )}
        
        {candidate && !feedback && (
          <ChatWindow 
            sessionId={sessionId} 
            candidate={candidate} 
            onComplete={handleComplete} 
          />
        )}
        
        {feedback && (
          <FeedbackPanel feedback={feedback} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;
