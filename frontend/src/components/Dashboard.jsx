import React, { useEffect, useState } from 'react';
import { Flame, Trophy, CheckCircle, BarChart3, Clock, Sparkles, Plus, X, Calendar, AlertTriangle, Trash } from 'lucide-react';

function Dashboard({ onSelectProblem }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Custom Goal Form State
  const [showModal, setShowModal] = useState(false);
  const [newGoalTitle, setNewGoalTitle] = useState('');
  const [newGoalDesc, setNewGoalDesc] = useState('');
  const [newGoalCategory, setNewGoalCategory] = useState('All');
  const [newGoalTarget, setNewGoalTarget] = useState(5);
  const [newGoalEndDate, setNewGoalEndDate] = useState('');
  const [newGoalPriority, setNewGoalPriority] = useState('Medium');

  const fetchDashboardData = () => {
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
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleCreateCustomGoal = (e) => {
    e.preventDefault();
    if (!newGoalTitle.trim()) return;

    const payload = {
      type: 'Custom',
      title: newGoalTitle,
      description: newGoalDesc,
      category: newGoalCategory === 'All' ? '' : newGoalCategory,
      target: parseInt(newGoalTarget),
      end_date: newGoalEndDate || null,
      priority: newGoalPriority,
      status: 'Not Started',
      start_date: new Date().toISOString().split('T')[0]
    };

    fetch('http://localhost:8000/api/goals/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then(res => res.json())
      .then(() => {
        setShowModal(false);
        // Clear form
        setNewGoalTitle('');
        setNewGoalDesc('');
        setNewGoalCategory('All');
        setNewGoalTarget(5);
        setNewGoalEndDate('');
        setNewGoalPriority('Medium');
        fetchDashboardData();
      })
      .catch(err => console.error(err));
  };

  const handleDeleteGoal = (goalId) => {
    if (!window.confirm("Are you sure you want to delete this goal?")) return;
    fetch(`http://localhost:8000/api/goals/${goalId}/`, {
      method: 'DELETE',
    })
      .then(() => {
        fetchDashboardData();
      })
      .catch(err => console.error(err));
  };

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

          {/* Goals Section */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Trophy size={18} color="#ffb300" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Active Goals</h4>
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                onClick={() => setShowModal(true)}
              >
                <Plus size={12} /> Add Custom
              </button>
            </div>

            {data.active_goals && data.active_goals.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '1rem 0' }}>
                No active goals. Click Add Custom to create one!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {data.active_goals && data.active_goals.map((goal) => {
                  const percent = goal.target > 0 ? Math.round((goal.progress / goal.target) * 100) : 0;
                  return (
                    <div 
                      key={goal.id} 
                      style={{ 
                        background: 'rgba(255,255,255,0.02)', 
                        border: '1px solid var(--border-glass)', 
                        borderRadius: '8px', 
                        padding: '1rem',
                        position: 'relative'
                      }}
                    >
                      {goal.type === 'Custom' && (
                        <button 
                          style={{ position: 'absolute', right: '0.5rem', top: '0.5rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                          onClick={() => handleDeleteGoal(goal.id)}
                          title="Delete Goal"
                        >
                          <Trash size={12} />
                        </button>
                      )}
                      
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem', paddingRight: '1.5rem' }}>
                        {goal.title || `${goal.type} Goal`}
                      </div>

                      {goal.category && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                          Category: {goal.category}
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem', color: 'var(--text-secondary)' }}>
                        <span>Progress: {goal.progress} / {goal.target}</span>
                        <span>{percent}%</span>
                      </div>

                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.5rem' }}>
                        <div style={{ height: '100%', background: 'linear-gradient(90deg, #ffb300, #ff8f00)', width: `${Math.min(100, percent)}%` }} />
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        <span>Target: {goal.end_date || 'None'}</span>
                        {goal.days_remaining !== null && (
                          <span style={{ color: goal.days_remaining <= 2 ? '#ff4b4b' : 'var(--text-muted)', fontWeight: 600 }}>
                            {goal.days_remaining} days left
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Create Custom Goal Modal Overlay */}
          {showModal && (
            <div style={{ 
              position: 'fixed', 
              top: 0, 
              left: 0, 
              right: 0, 
              bottom: 0, 
              backgroundColor: 'rgba(0,0,0,0.7)', 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              zIndex: 1000,
              backdropFilter: 'blur(4px)'
            }}>
              <div className="glass-panel" style={{ width: '450px', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Create Custom Goal</h3>
                  <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}>
                    <X size={20} />
                  </button>
                </div>

                <form onSubmit={handleCreateCustomGoal} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Goal Title</label>
                    <input 
                      type="text" 
                      required
                      placeholder="e.g. Master joins this week" 
                      value={newGoalTitle}
                      onChange={(e) => setNewGoalTitle(e.target.value)}
                      style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Description</label>
                    <textarea 
                      placeholder="Goal description..." 
                      value={newGoalDesc}
                      onChange={(e) => setNewGoalDesc(e.target.value)}
                      style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none', height: '60px', resize: 'none' }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Category</label>
                      <select 
                        value={newGoalCategory}
                        onChange={(e) => setNewGoalCategory(e.target.value)}
                        style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                      >
                        <option value="All">All Categories</option>
                        <option value="Filtering & Sorting">Filtering & Sorting</option>
                        <option value="Date & String">Date & String</option>
                        <option value="Aggregations">Aggregations</option>
                        <option value="Joins">Joins</option>
                        <option value="Advanced Nested & Pivot">Advanced Nested & Pivot</option>
                        <option value="Window Functions">Window Functions</option>
                        <option value="Data Cleaning & Null Handling">Data Cleaning & Null Handling</option>
                        <option value="Performance & Optimization">Performance & Optimization</option>
                        <option value="Array & Map Operations">Array & Map Operations</option>
                        <option value="User Defined Functions (UDFs)">UDFs</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Target problems count</label>
                      <input 
                        type="number" 
                        min="1"
                        required
                        value={newGoalTarget}
                        onChange={(e) => setNewGoalTarget(e.target.value)}
                        style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Target completion date</label>
                      <input 
                        type="date" 
                        value={newGoalEndDate}
                        onChange={(e) => setNewGoalEndDate(e.target.value)}
                        style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Priority</label>
                      <select 
                        value={newGoalPriority}
                        onChange={(e) => setNewGoalPriority(e.target.value)}
                        style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                      >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                      </select>
                    </div>
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>Create Goal</button>
                </form>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

export default Dashboard;
