import React, { useEffect, useState } from 'react';
import { Trophy, Award, Calendar, CheckCircle2, ShieldAlert, Sparkles, Star, Compass } from 'lucide-react';

function Achievements() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/achievements/')
      .then(res => res.json())
      .then(resData => {
        setData(resData);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading Achievements...</div>;
  }

  if (!data) {
    return <div style={{ color: 'var(--error)' }}>Failed to load achievements. Check backend connection.</div>;
  }

  const iconMap = {
    Award: Award,
    Trophy: Trophy,
    ShieldAlert: ShieldAlert,
    Sparkles: Sparkles,
    Star: Star,
    Compass: Compass
  };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Achievements</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Your completed goals, milestones, and earned challenges badges</p>
      </div>

      {/* Earned Badges Section */}
      <div style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Award color="var(--primary)" size={24} />
          Earned Badges ({data.badges.length})
        </h2>
        {data.badges.length === 0 ? (
          <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Award size={48} style={{ opacity: 0.2, marginBottom: '1rem', display: 'block', margin: '0 auto' }} />
            No badges earned yet. Go to <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Challenges</span> to complete problem sets and earn badges!
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
            {data.badges.map((badge) => {
              const IconComponent = iconMap[badge.badge_icon] || Award;
              return (
                <div 
                  key={badge.id} 
                  className="glass-panel" 
                  style={{ 
                    padding: '1.5rem', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    textAlign: 'center',
                    border: '1px solid rgba(255, 75, 75, 0.2)',
                    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 75, 75, 0.05))',
                    boxShadow: '0 8px 32px 0 rgba(255, 75, 75, 0.05)'
                  }}
                >
                  <div style={{ 
                    background: 'rgba(255, 75, 75, 0.1)', 
                    color: 'var(--primary)', 
                    padding: '1rem', 
                    borderRadius: '50%',
                    marginBottom: '1rem',
                    boxShadow: '0 0 15px rgba(255, 75, 75, 0.2)'
                  }}>
                    <IconComponent size={36} />
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.25rem' }}>{badge.badge_name}</h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>{badge.name}</span>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem', flex: 1 }}>{badge.description}</p>
                  
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '0.4rem 0.8rem', borderRadius: '20px' }}>
                    <Calendar size={12} />
                    <span>Earned: {badge.completion_date}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Completed Goals Section */}
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Trophy color="#ffb300" size={24} />
          Completed Goals ({data.goals.length})
        </h2>
        {data.goals.length === 0 ? (
          <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Trophy size={48} style={{ opacity: 0.2, marginBottom: '1rem', display: 'block', margin: '0 auto' }} />
            No goals completed yet. Set active goals on your <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Dashboard</span> and solve problems to complete them!
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {data.goals.map((goal) => (
              <div 
                key={goal.id} 
                className="glass-panel" 
                style={{ 
                  padding: '1.5rem', 
                  borderLeft: '4px solid var(--success)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                      {goal.title || `${goal.type} Goal`}
                    </h3>
                    {goal.category && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Category: {goal.category}
                      </span>
                    )}
                  </div>
                  <CheckCircle2 color="var(--success)" size={20} />
                </div>
                
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                  {goal.description || `Successfully solved ${goal.target} Spark problems.`}
                </p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '0.5rem', fontSize: '0.75rem', borderTop: '1px solid var(--border-glass)', paddingTop: '0.75rem' }}>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Target: <strong style={{ color: 'var(--text-primary)' }}>{goal.target} Problems</strong>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Time Taken: <strong style={{ color: 'var(--text-primary)' }}>{goal.time_taken || 'N/A'}</strong>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Completed: <strong style={{ color: 'var(--text-primary)' }}>{goal.completion_date}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Achievements;
