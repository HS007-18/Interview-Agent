import React, { useEffect, useState } from 'react';

export default function CandidateSelect({ onSelect }) {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch('/api/candidates')
      .then(res => res.json())
      .then(data => {
        setCandidates(data.candidates || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load candidates. Please ensure backend server is running.');
        setLoading(false);
      });
  }, []);

  const getInitials = (name = 'Unknown') => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const filteredCandidates = candidates.filter(c => {
    const name = c.member?.name?.toLowerCase() || '';
    const role = c.member?.jobRole?.toLowerCase() || '';
    const edu = c.member?.education?.toLowerCase() || '';
    const term = searchTerm.toLowerCase();
    return name.includes(term) || role.includes(term) || edu.includes(term);
  });

  if (loading) {
    return (
      <div className="loading-box">
        <div className="spinner"></div>
        <span>Loading candidate profiles...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="candidate-select">
      <div className="select-header-bar">
        <div className="select-title-group">
          <h2>Select Candidate for Technical Assessment</h2>
          <p>Choose a candidate profile to initiate an AI-conducted technical interview</p>
        </div>

        {candidates.length > 0 && (
          <div className="search-box">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input 
              type="text" 
              placeholder="Search candidate or role..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        )}
      </div>

      {filteredCandidates.length === 0 ? (
        <div className="loading-box">
          <span>No candidates found matching "{searchTerm}"</span>
        </div>
      ) : (
        <div className="candidate-grid">
          {filteredCandidates.map((c, idx) => {
            const candidateName = c.member?.name || 'Unknown Candidate';
            const statusClass = c.member?.status?.toLowerCase() || 'unknown';
            
            return (
              <div key={idx} className="candidate-card" onClick={() => onSelect(c)}>
                <div className="card-top">
                  <div className="avatar-circle">
                    {getInitials(candidateName)}
                  </div>
                  <div className="candidate-identity">
                    <h3>{candidateName}</h3>
                    <p className="role">{c.member?.jobRole || 'Technical Candidate'}</p>
                  </div>
                  <span className={`status-badge ${statusClass}`}>
                    {c.member?.status || 'Available'}
                  </span>
                </div>

                <div className="card-details-pills">
                  {c.member?.yearsExperience !== undefined && (
                    <span className="detail-pill">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                      </svg>
                      {c.member?.yearsExperience} YOE
                    </span>
                  )}
                  {c.member?.education && (
                    <span className="detail-pill">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
                        <path d="M6 12v5c3 3 9 3 12 0v-5"></path>
                      </svg>
                      {c.member?.education}
                    </span>
                  )}
                </div>

                <button className="select-btn">
                  Start Technical Interview
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
