import React from 'react';

export default function FeedbackPanel({ feedback, onReset }) {
  if (!feedback) return null;

  return (
    <div className="feedback-panel">
      <div className="feedback-header">
        <div className="feedback-title-group">
          <h2>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--strength-color)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            Technical Assessment Report
          </h2>
          <p>AI-conducted evaluation summary and candidate scorecard</p>
        </div>
        <span className="badge-complete">Completed</span>
      </div>
      
      <div className="feedback-summary-card">
        <h3>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          Executive Summary
        </h3>
        <p>{feedback.summary || 'No summary provided.'}</p>
      </div>
      
      <div className="feedback-cards-grid">
        <div className="feedback-card strengths">
          <h3>
            <span className="card-icon-badge">✓</span>
            Demonstrated Strengths
          </h3>
          <ul>
            {feedback.strengths && feedback.strengths.length > 0 ? (
              feedback.strengths.map((item, i) => <li key={i}>{item}</li>)
            ) : (
              <li>No key strengths noted.</li>
            )}
          </ul>
        </div>
        
        <div className="feedback-card gaps">
          <h3>
            <span className="card-icon-badge">!</span>
            Knowledge Gaps & Areas to Improve
          </h3>
          <ul>
            {feedback.gaps && feedback.gaps.length > 0 ? (
              feedback.gaps.map((item, i) => <li key={i}>{item}</li>)
            ) : (
              <li>No significant gaps identified.</li>
            )}
          </ul>
        </div>
        
        <div className="feedback-card next">
          <h3>
            <span className="card-icon-badge">→</span>
            Recommended Next Steps
          </h3>
          <ul>
            {feedback.next && feedback.next.length > 0 ? (
              feedback.next.map((item, i) => <li key={i}>{item}</li>)
            ) : (
              <li>No specific next steps recommended.</li>
            )}
          </ul>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '8px' }}>
        <button className="reset-btn" onClick={onReset}>
          Assess Another Candidate
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </div>
    </div>
  );
}
