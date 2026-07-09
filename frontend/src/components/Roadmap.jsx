import React, { useEffect, useState } from 'react';
import { ToggleLeft, ToggleRight, Compass, ShieldAlert, Award, Star, Trophy, ChevronDown, ChevronUp, Clock, CheckCircle2, Play } from 'lucide-react';

function Roadmap({ onSelectProblem }) {
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedLevels, setExpandedLevels] = useState({});

  useEffect(() => {
    fetchRoadmaps();
  }, []);

  const fetchRoadmaps = () => {
    fetch('http://localhost:8000/api/roadmaps/')
      .then(res => res.json())
      .then(data => {
        setRoadmaps(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleToggleOptIn = (level, currentOpt) => {
    fetch('http://localhost:8000/api/roadmaps/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        level: level,
        opted_in: !currentOpt
      })
    })
      .then(res => res.json())
      .then(() => {
        fetchRoadmaps();
      });
  };

  const toggleExpand = (level) => {
    setExpandedLevels(prev => ({
      ...prev,
      [level]: !prev[level]
    }));
  };

  if (loading) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading roadmaps...</div>;
  }

  // Level info mapper
  const levelDetails = {
    Beginner: { desc: 'PySpark basics, basic DataFrame creation, and single-table select/filter operations.', color: '#00e676', icon: Compass },
    Intermediate: { desc: 'Aggregations, group-bys, column operations, and multiple-dataset inner/outer joins.', color: '#00f2fe', icon: Star },
    Advanced: { desc: 'Window functions, analytical partitioning, pivoting, nested struct array/map explosion.', color: '#ffb300', icon: Award },
    Expert: { desc: 'Custom User Defined Functions (UDFs), data cleaning, regex extraction, null filling.', color: '#ff4b4b', icon: ShieldAlert },
    Master: { desc: 'Performance tuning, query optimization, repartitioning vs coalescing, broadcast joins.', color: '#d500f9', icon: Trophy }
  };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Learning Campaigns</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Opt in to progressive learning levels to customize your daily problems mission and preview campaigns</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {roadmaps.map((rm) => {
          const detail = levelDetails[rm.level] || { desc: '', color: '#fff', icon: Compass };
          const Icon = detail.icon;
          const isExpanded = !!expandedLevels[rm.level];
          
          return (
            <div 
              key={rm.level} 
              className="glass-panel" 
              style={{ 
                padding: '2rem', 
                borderLeft: `5px solid ${detail.color}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '1.5rem'
              }}
            >
              {/* Header row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '2rem' }}>
                <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
                  <div style={{ 
                    background: 'rgba(255,255,255,0.03)', 
                    border: '1px solid var(--border-glass)', 
                    borderRadius: '12px', 
                    padding: '0.75rem',
                    color: detail.color
                  }}>
                    <Icon size={28} />
                  </div>
                  
                  <div>
                    <h3 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {rm.level} Campaign
                      {rm.opted_in && (
                        <span className="badge" style={{ background: 'rgba(0, 230, 118, 0.1)', color: '#00e676', fontSize: '0.675rem' }}>
                          ACTIVE TARGET
                        </span>
                      )}
                    </h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5', margin: 0 }}>
                      {detail.desc}
                    </p>
                  </div>
                </div>

                {/* Opt-in switch */}
                <div 
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
                  onClick={() => handleToggleOptIn(rm.level, rm.opted_in)}
                >
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: rm.opted_in ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                    {rm.opted_in ? 'ACTIVE' : 'START'}
                  </span>
                  {rm.opted_in ? (
                    <ToggleRight size={38} color="#00e676" />
                  ) : (
                    <ToggleLeft size={38} color="var(--text-muted)" />
                  )}
                </div>
              </div>

              {/* Progress and metadata row */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1.5fr', gap: '2rem', background: 'rgba(0,0,0,0.15)', padding: '1rem 1.5rem', borderRadius: '10px', fontSize: '0.85rem' }}>
                {/* Progress bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', color: 'var(--text-secondary)' }}>
                    <span>Progress</span>
                    <span>{rm.completed_problems_count} / {rm.total_problems} Solved</span>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: detail.color, width: `${rm.completion_percentage}%` }} />
                  </div>
                </div>

                {/* Est time remaining */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                  <Clock size={16} />
                  <span>Time Left: <strong>{rm.estimated_time_minutes} mins</strong></span>
                </div>

                {/* Skills tags */}
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.25rem' }}>SKILLS COVERED</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                    {rm.skills_covered.map((skill, idx) => (
                      <span key={idx} className="badge badge-category" style={{ fontSize: '0.65rem', padding: '0.2rem 0.5rem' }}>{skill}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Preview problems toggle */}
              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
                <button 
                  className="btn btn-secondary" 
                  style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}
                  onClick={() => toggleExpand(rm.level)}
                >
                  {isExpanded ? (
                    <>Hide Problems Preview <ChevronUp size={16} /></>
                  ) : (
                    <>Preview Campaign Problems ({rm.problems.length}) <ChevronDown size={16} /></>
                  )}
                </button>

                {isExpanded && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
                    {rm.problems.map((prob) => (
                      <div 
                        key={prob.id} 
                        style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center', 
                          padding: '0.75rem 1rem', 
                          background: 'rgba(255,255,255,0.01)', 
                          border: '1px solid var(--border-glass)', 
                          borderRadius: '8px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          {prob.is_solved ? (
                            <CheckCircle2 size={16} color="var(--success)" />
                          ) : (
                            <Clock size={16} color="var(--text-muted)" />
                          )}
                          <span style={{ fontWeight: 500, fontSize: '0.9rem', color: prob.is_solved ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                            {prob.title}
                          </span>
                          <span className={`badge badge-${prob.difficulty.toLowerCase()}`} style={{ fontSize: '0.675rem' }}>
                            {prob.difficulty}
                          </span>
                        </div>
                        <button 
                          className="btn btn-primary" 
                          style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                          onClick={() => onSelectProblem(prob.id)}
                        >
                          <Play size={10} fill="currentColor" /> Solve
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Roadmap;
