import React, { useEffect, useState } from 'react';
import { ToggleLeft, ToggleRight, Compass, ShieldAlert, Award, Star, Trophy } from 'lucide-react';

function Roadmap({ onSelectProblem }) {
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);

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
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Learning Roadmaps</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Opt in to progressive learning levels to customize your daily problems mission</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {roadmaps.map((rm) => {
          const detail = levelDetails[rm.level] || { desc: '', color: '#fff', icon: Compass };
          const Icon = detail.icon;
          
          return (
            <div 
              key={rm.level} 
              className="glass-panel" 
              style={{ 
                padding: '1.75rem', 
                borderLeft: `5px solid ${detail.color}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '2rem'
              }}
            >
              <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'flex-start' }}>
                <div style={{ 
                  background: 'rgba(255,255,255,0.03)', 
                  border: '1px solid var(--border-glass)', 
                  borderRadius: '12px', 
                  padding: '0.75rem',
                  color: detail.color
                }}>
                  <Icon size={28} />
                </div>
                
                <div style={{ maxWidth: '600px' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {rm.level} Roadmap
                    {rm.opted_in && (
                      <span className="badge" style={{ background: 'rgba(0, 230, 118, 0.1)', color: '#00e676', fontSize: '0.675rem' }}>
                        ACTIVE TARGET
                      </span>
                    )}
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
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
                  {rm.opted_in ? 'OPTED IN' : 'OPT OUT'}
                </span>
                {rm.opted_in ? (
                  <ToggleRight size={38} color="#00e676" />
                ) : (
                  <ToggleLeft size={38} color="var(--text-muted)" />
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
