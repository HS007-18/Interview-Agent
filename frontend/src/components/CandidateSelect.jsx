import React, { useEffect, useState } from 'react';

export default function CandidateSelect({ onSelect }) {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/candidates')
      .then(res => res.json())
      .then(data => {
        setCandidates(data.candidates || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load candidates.');
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="loading">Loading candidates...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="candidate-select">
      <h2>Select a Candidate to Interview</h2>
      <div className="candidate-grid">
        {candidates.map((c, idx) => (
          <div key={idx} className="candidate-card" onClick={() => onSelect(c)}>
            <div className="card-header">
              <h3>{c.member?.name || 'Unknown Candidate'}</h3>
              <span className={`status-badge ${c.member?.status?.toLowerCase() || 'unknown'}`}>{c.member?.status || 'Unknown'}</span>
            </div>
            <p className="role">{c.member?.jobRole}</p>
            <div className="card-details">
              <span className="experience">{c.member?.yearsExperience} YOE</span>
              <span className="education">{c.member?.education}</span>
            </div>
            <button className="select-btn">Start Interview</button>
          </div>
        ))}
      </div>
    </div>
  );
}
