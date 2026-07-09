import React, { useEffect, useState } from 'react';
import { Search, Building2, ChevronRight, BarChart2, CheckCircle2, Circle, ArrowLeft, Briefcase, Award } from 'lucide-react';

function CompanyExplorer({ onSelectProblem }) {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyDetails, setCompanyDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/companies/')
      .then(res => res.json())
      .then(data => {
        setCompanies(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const handleSelectCompany = (companyName) => {
    setSelectedCompany(companyName);
    setLoadingDetails(true);
    fetch(`http://localhost:8000/api/companies/${companyName}/`)
      .then(res => res.json())
      .then(data => {
        setCompanyDetails(data);
        setLoadingDetails(false);
      })
      .catch(err => {
        console.error(err);
        setLoadingDetails(false);
      });
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading Company Explorer...</div>;
  }

  // Detailed Company View
  if (selectedCompany && companyDetails) {
    const details = companyDetails;
    return (
      <div>
        <button 
          className="btn btn-secondary" 
          style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          onClick={() => { setSelectedCompany(null); setCompanyDetails(null); }}
        >
          <ArrowLeft size={16} /> Back to Companies
        </button>

        <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <Building2 size={32} color="var(--primary)" />
              <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>{details.name}</h1>
            </div>
            <p style={{ color: 'var(--text-secondary)' }}>Targeted preparation for {details.name} Spark interviews</p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.25rem' }}>
              COMPLETION RATE
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)' }}>
              {details.completion_percentage}%
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {details.completed_problems_count} of {details.total_problems} solved
            </div>
          </div>
        </div>

        {/* Info Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', marginBottom: '2rem' }}>
          {/* Left Stats card */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Difficulty breakdown */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.25rem' }}>Difficulty Distribution</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {Object.entries(details.difficulty_distribution).map(([diff, count]) => {
                  const percent = details.total_problems > 0 ? (count / details.total_problems * 100) : 0;
                  const color = diff === 'Easy' ? '#00e676' : diff === 'Medium' ? '#00f2fe' : '#ff4b4b';
                  return (
                    <div key={diff}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                        <span>{diff}</span>
                        <span>{count} ({Math.round(percent)}%)</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: color, width: `${percent}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Frequent topics */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>Frequent Topics</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {details.frequent_topics.map((topic, idx) => (
                  <span key={idx} className="badge badge-category" style={{ fontSize: '0.75rem', padding: '0.4rem 0.8rem', borderRadius: '12px' }}>
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right Problems list */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1.25rem' }}>Interview Questions ({details.problems.length})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {details.problems.map((prob) => {
                const freqColor = prob.frequency === 'Frequently Asked' ? 'rgba(255, 75, 75, 0.15)' : prob.frequency === 'Occasionally Asked' ? 'rgba(255, 179, 0, 0.15)' : 'rgba(255,255,255,0.05)';
                const freqText = prob.frequency === 'Frequently Asked' ? '#ff4b4b' : prob.frequency === 'Occasionally Asked' ? '#ffb300' : 'var(--text-muted)';
                
                return (
                  <div 
                    key={prob.id} 
                    style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      padding: '1rem', 
                      background: 'rgba(255,255,255,0.02)', 
                      border: '1px solid var(--border-glass)', 
                      borderRadius: '10px'
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {prob.is_solved ? (
                          <CheckCircle2 size={16} color="var(--success)" />
                        ) : (
                          <Circle size={16} color="var(--text-muted)" />
                        )}
                        <span style={{ fontWeight: 600, color: prob.is_solved ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                          {prob.title}
                        </span>
                        <span className={`badge badge-${prob.difficulty.toLowerCase()}`} style={{ fontSize: '0.675rem' }}>
                          {prob.difficulty}
                        </span>
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>{prob.category}</span>
                        <span>•</span>
                        <span style={{ color: freqText, background: freqColor, padding: '0.1rem 0.4rem', borderRadius: '4px', fontWeight: 600 }}>
                          {prob.frequency}
                        </span>
                      </div>
                    </div>

                    <button 
                      className="btn btn-primary" 
                      style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}
                      onClick={() => onSelectProblem(prob.id)}
                    >
                      Solve
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Company Grid View
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Company Explorer</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Browse interview problems from top product companies and target your preparation</p>
        </div>

        {/* Search Bar */}
        <div style={{ position: 'relative', width: '300px' }}>
          <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search companies..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '0.75rem 1rem 0.75rem 2.5rem', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-glass)', 
              borderRadius: '24px', 
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {filteredCompanies.map((c) => (
          <div 
            key={c.name} 
            className="glass-panel" 
            style={{ 
              padding: '1.5rem', 
              cursor: 'pointer', 
              transition: 'transform 0.2s, border-color 0.2s',
              border: '1px solid var(--border-glass)'
            }}
            onClick={() => handleSelectCompany(c.name)}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border-glass)'; e.currentTarget.style.transform = 'none'; }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.5rem', borderRadius: '8px' }}>
                  <Building2 size={20} color="var(--primary)" />
                </div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>{c.name}</h3>
              </div>
              <ChevronRight size={18} color="var(--text-muted)" />
            </div>

            {/* Metrics */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
              <span>Problems: <strong>{c.total_problems}</strong></span>
              <span style={{ color: 'var(--success)' }}>Solved: <strong>{c.completed_problems_count}</strong></span>
            </div>

            {/* Progress bar */}
            <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden', marginBottom: '1rem' }}>
              <div style={{ height: '100%', background: 'var(--success)', width: `${c.completion_percentage}%` }} />
            </div>

            {/* Difficulty badge counts */}
            <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.7rem' }}>
              <span className="badge badge-easy">E: {c.difficulty_distribution.Easy}</span>
              <span className="badge badge-medium">M: {c.difficulty_distribution.Medium}</span>
              <span className="badge badge-hard">H: {c.difficulty_distribution.Hard}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default CompanyExplorer;
