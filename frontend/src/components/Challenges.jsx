import React, { useEffect, useState } from 'react';
import { Award, CheckCircle, Lock, Play, ShieldAlert, Sparkles, Star, Compass, AlertCircle } from 'lucide-react';

function Challenges({ onSelectProblem }) {
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/challenges/status/')
      .then(res => res.json())
      .then(data => {
        setChallenges(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading Challenges...</div>;
  }

  const iconMap = {
    Award: Award,
    ShieldAlert: ShieldAlert,
    Sparkles: Sparkles,
    Star: Star,
    Compass: Compass
  };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Custom Challenges</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Complete curated problem sets to unlock badges and display them on your achievements profile</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
        {challenges.map((ch) => {
          const IconComponent = iconMap[ch.badge_icon] || Award;
          const statusText = ch.is_unlocked ? "UNLOCKED" : ch.completed_problems_count > 0 ? "IN PROGRESS" : "LOCKED";
          const statusColor = ch.is_unlocked ? "var(--success)" : ch.completed_problems_count > 0 ? "var(--primary)" : "var(--text-muted)";
          
          return (
            <div 
              key={ch.id} 
              className="glass-panel" 
              style={{ 
                padding: '2rem',
                borderLeft: `5px solid ${statusColor}`,
                display: 'grid',
                gridTemplateColumns: '1fr 2fr',
                gap: '2rem',
                alignItems: 'start'
              }}
            >
              {/* Badge Panel */}
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                textAlign: 'center', 
                background: 'rgba(255,255,255,0.01)', 
                border: '1px solid var(--border-glass)',
                padding: '1.5rem',
                borderRadius: '16px'
              }}>
                <div style={{ 
                  background: ch.is_unlocked ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255,255,255,0.03)', 
                  color: ch.is_unlocked ? 'var(--success)' : 'var(--text-muted)', 
                  padding: '1.25rem', 
                  borderRadius: '50%',
                  marginBottom: '1rem',
                  boxShadow: ch.is_unlocked ? '0 0 20px rgba(0, 230, 118, 0.2)' : 'none'
                }}>
                  <IconComponent size={44} />
                </div>
                
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.25rem' }}>{ch.badge_name}</h3>
                <span className="badge" style={{ 
                  background: ch.is_unlocked ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255,255,255,0.05)',
                  color: statusColor,
                  fontWeight: 700,
                  fontSize: '0.7rem',
                  letterSpacing: '0.05em'
                }}>
                  {statusText}
                </span>

                <div style={{ width: '100%', marginTop: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    <span>Progress</span>
                    <span>{ch.completed_problems_count} / {ch.total_problems} solved</span>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div 
                      style={{ 
                        height: '100%', 
                        background: ch.is_unlocked ? 'var(--success)' : 'var(--primary)', 
                        width: `${ch.completion_percentage}%`,
                        transition: 'width 0.5s ease'
                      }} 
                    />
                  </div>
                </div>
              </div>

              {/* Info & Problems Panel */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>{ch.name}</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
                    {ch.description}
                  </p>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Included Problems
                  </h4>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {ch.problems.map((prob) => (
                      <div 
                        key={prob.id} 
                        style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center', 
                          padding: '0.75rem 1rem', 
                          background: 'rgba(255,255,255,0.02)', 
                          border: '1px solid var(--border-glass)', 
                          borderRadius: '8px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          {prob.is_solved ? (
                            <CheckCircle size={16} color="var(--success)" />
                          ) : (
                            <AlertCircle size={16} color="var(--text-muted)" />
                          )}
                          <span style={{ fontWeight: 500, fontSize: '0.9rem', color: prob.is_solved ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                            {prob.title}
                          </span>
                          <span className={`badge badge-${prob.difficulty.toLowerCase()}`} style={{ fontSize: '0.675rem' }}>
                            {prob.difficulty}
                          </span>
                        </div>

                        <button 
                          className="btn btn-secondary" 
                          style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                          onClick={() => onSelectProblem(prob.id)}
                        >
                          <Play size={10} fill="currentColor" />
                          Solve
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Challenges;
