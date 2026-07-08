import React, { useEffect, useState } from 'react';
import { Flame, Trophy, CheckCircle, BarChart3, Clock, Sparkles } from 'lucide-react';

function Dashboard({ onSelectProblem }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/dashboard/')
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
    return <div style={{ color: 'var(--text-secondary)' }}>Loading Dashboard metrics...</div>;
  }

  if (!data) {
    return <div style={{ color: 'var(--error)' }}>Failed to load dashboard data. Check backend connection.</div>;
  }

  // Generate heatmap grid for 53 weeks
  const renderHeatmap = () => {
    const dates = [];
    const today = new Date();
    // 365 days ago
    const start = new Date(today);
    start.setDate(start.getDate() - 365);
    
    // Find first Sunday to align days of week
    const dayOfWeek = start.getDay();
    start.setDate(start.getDate() - dayOfWeek);

    const temp = new Date(start);
    while (temp <= today) {
      dates.push(new Date(temp));
      temp.setDate(temp.getDate() + 1);
    }

    return (
      <div className="heatmap-grid" style={{ gridAutoFlow: 'column', gridTemplateRows: 'repeat(7, 12px)', gap: '4px' }}>
        {dates.map((date, idx) => {
          const dateStr = date.toISOString().split('T')[0];
          const activity = data.heatmap_data[dateStr] || { attempts: 0, solved: 0 };
          
          let levelClass = '';
          if (activity.solved > 0) {
            levelClass = activity.solved >= 3 ? 'level-4' : activity.solved === 2 ? 'level-3' : 'level-2';
          } else if (activity.attempts > 0) {
            levelClass = 'level-1';
          }

          return (
            <div 
              key={idx}
              className={`heatmap-cell ${levelClass}`}
              title={`${dateStr}: ${activity.solved} solved, ${activity.attempts} attempts`}
              style={{ width: '12px', height: '12px', borderRadius: '2px', cursor: 'pointer' }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Track your daily PySpark coding journey & streak status</p>
        </div>
        
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1.25rem' }}>
          <Flame color="#ff4b4b" fill="#ff4b4b" size={24} />
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>CURRENT STREAK</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{data.current_streak} Days</div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metric-grid">
        <div className="glass-panel metric-card">
          <span className="label">Streak Records</span>
          <span className="value" style={{ color: '#ff4b4b', textShadow: '0 0 15px rgba(255, 75, 75, 0.2)' }}>
            {data.current_streak} / {data.longest_streak}
          </span>
          <span className="subtext">Current streak vs Longest streak</span>
        </div>
        
        <div className="glass-panel metric-card">
          <span className="label">Problems Solved</span>
          <span className="value" style={{ color: '#00f2fe', textShadow: '0 0 15px rgba(0, 242, 254, 0.2)' }}>
            {data.problems_solved} / {data.total_problems}
          </span>
          <span className="subtext">{data.problems_attempted} total attempted</span>
        </div>
        
        <div className="glass-panel metric-card">
          <span className="label">Success Rate</span>
          <span className="value" style={{ color: '#00e676', textShadow: '0 0 15px rgba(0, 230, 118, 0.2)' }}>
            {data.success_rate}%
          </span>
          <span className="subtext">Passed vs Attempted problems</span>
        </div>
        
        <div className="glass-panel metric-card">
          <span className="label">Spark Executions</span>
          <span className="value" style={{ color: '#ffb300', textShadow: '0 0 15px rgba(255, 179, 0, 0.2)' }}>
            {data.spark_jobs_executed}
          </span>
          <span className="subtext">Spark jobs executed successfully</span>
        </div>
      </div>

      {/* Main Grid Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        
        {/* Heatmap Card */}
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <BarChart3 size={20} color="var(--primary)" />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Activity Heatmap</h3>
          </div>
          
          <div style={{ overflowX: 'auto' }}>
            {renderHeatmap()}
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <span>Less</span>
            <div style={{ width: '10px', height: '10px', background: '#161b22', borderRadius: '2px' }} />
            <div style={{ width: '10px', height: '10px', background: 'rgba(0, 230, 118, 0.2)', borderRadius: '2px' }} />
            <div style={{ width: '10px', height: '10px', background: 'rgba(0, 230, 118, 0.4)', borderRadius: '2px' }} />
            <div style={{ width: '10px', height: '10px', background: 'rgba(0, 230, 118, 0.7)', borderRadius: '2px' }} />
            <div style={{ width: '10px', height: '10px', background: 'var(--success)', borderRadius: '2px' }} />
            <span>More</span>
          </div>
        </div>

        {/* Side panels (Mission + Goals) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Today's Mission */}
          {data.today_mission && (
            <div className="glass-panel" style={{ padding: '1.5rem', borderLeft: '4px solid var(--primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Sparkles size={18} color="var(--primary)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Today's Mission</h4>
              </div>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: '0.25rem' }}>
                {data.today_mission.title}
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <span className={`badge badge-${data.today_mission.difficulty.toLowerCase()}`}>
                  {data.today_mission.difficulty}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {data.today_mission.category}
                </span>
              </div>
              <button 
                className="btn btn-primary" 
                style={{ width: '100%', fontSize: '0.875rem' }}
                onClick={() => onSelectProblem(data.today_mission.id)}
              >
                Start Solving
              </button>
            </div>
          )}

          {/* Monthly Goal Progress */}
          {data.monthly_goal && (
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                <Trophy size={18} color="#ffb300" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Monthly Goal</h4>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                <span>Solved: {data.monthly_goal.progress} / {data.monthly_goal.target}</span>
                <span>{Math.round((data.monthly_goal.progress / data.monthly_goal.target) * 100)}%</span>
              </div>
              {/* Progress bar */}
              <div style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    height: '100%', 
                    background: 'linear-gradient(90deg, #ffb300, #ff8f00)', 
                    width: `${Math.min(100, (data.monthly_goal.progress / data.monthly_goal.target) * 100)}%` 
                  }} 
                />
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', textAlign: 'right' }}>
                Ends: {data.monthly_goal.end_date}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

export default Dashboard;
