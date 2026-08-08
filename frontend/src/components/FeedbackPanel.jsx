import React from 'react';

export default function FeedbackPanel({ feedback, onReset }) {
  if (!feedback) return null;

  return (
    <div className="feedback-panel">
      <h2>Interview Complete</h2>
      
      <div className="feedback-summary-card">
        <h3>Summary</h3>
        <p>{feedback.summary}</p>
      </div>
      
      <div className="feedback-cards">
        <div className="feedback-card strengths">
          <h3><span className="icon">✓</span> Strengths</h3>
          <ul>
            {feedback.strengths?.map((item, i) => <li key={i}>{item}</li>) || <li>None noted.</li>}
          </ul>
        </div>
        
        <div className="feedback-card gaps">
          <h3><span className="icon">!</span> Gaps</h3>
          <ul>
            {feedback.gaps?.map((item, i) => <li key={i}>{item}</li>) || <li>None noted.</li>}
          </ul>
        </div>
        
        <div className="feedback-card next">
          <h3><span className="icon">→</span> Next Steps</h3>
          <ul>
            {feedback.next?.map((item, i) => <li key={i}>{item}</li>) || <li>None noted.</li>}
          </ul>
        </div>
      </div>
      
      <button className="reset-btn" onClick={onReset}>Interview Another Candidate</button>
    </div>
  );
}
