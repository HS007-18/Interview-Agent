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
        <h1>AI Interviewer</h1>
        {candidate && <button className="header-reset" onClick={handleReset}>Back to Candidates</button>}
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
