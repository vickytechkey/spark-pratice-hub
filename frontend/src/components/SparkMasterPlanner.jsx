import React, { useState, useEffect, useRef } from 'react';
import { 
  BookOpen, Calendar, CheckCircle2, Clock, Play, Pause, RotateCcw, 
  Trophy, Award, Flame, Star, Zap, ChevronRight, Settings, AlertCircle 
} from 'lucide-react';

function SparkMasterPlanner() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  
  // Timer State
  const [timerMinutes, setTimerMinutes] = useState(30);
  const [timeLeft, setTimeLeft] = useState(30 * 60);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const timerRef = useRef(null);

  // Tab State
  const [activeTab, setActiveTab] = useState('schedule'); // 'schedule', 'syllabus', 'timer'

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = () => {
    setLoading(true);
    fetch('http://localhost:8000/api/spark_master/schedule/')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch Spark Master path data');
        return res.json();
      })
      .then(resData => {
        setData(resData);
        if (resData.schedules && resData.schedules.length > 0) {
          // Default select the first uncompleted or first schedule
          const todayOrNext = resData.schedules.find(s => !s.completed) || resData.schedules[0];
          setSelectedSchedule(todayOrNext);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  };

  const handleToggleComplete = (scheduleId, currentCompleted) => {
    fetch('http://localhost:8000/api/spark_master/log_session/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        schedule_id: scheduleId,
        completed: !currentCompleted
      })
    })
      .then(res => res.json())
      .then(() => {
        fetchData();
      })
      .catch(err => console.error(err));
  };

  const handleResetSchedule = (dateStr) => {
    if (!window.confirm(`Are you sure you want to reset and reschedule all topics starting from ${dateStr}?`)) {
      return;
    }
    fetch('http://localhost:8000/api/spark_master/reset_schedule/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_date: dateStr })
    })
      .then(res => res.json())
      .then(() => {
        fetchData();
      })
      .catch(err => console.error(err));
  };

  // Timer Handlers
  const startTimer = () => {
    if (isTimerRunning) return;
    setIsTimerRunning(true);
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          setIsTimerRunning(false);
          handleTimerComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const pauseTimer = () => {
    clearInterval(timerRef.current);
    setIsTimerRunning(false);
  };

  const resetTimer = () => {
    clearInterval(timerRef.current);
    setIsTimerRunning(false);
    setTimeLeft(timerMinutes * 60);
  };

  const handleCustomMinutesChange = (mins) => {
    const validMins = Math.max(1, Math.min(180, parseInt(mins) || 0));
    setTimerMinutes(validMins);
    setTimeLeft(validMins * 60);
  };

  const handleTimerComplete = () => {
    alert(`🎉 Excellent! You have completed a ${timerMinutes}-minute focus session!`);
    if (selectedSchedule) {
      fetch('http://localhost:8000/api/spark_master/log_session/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schedule_id: selectedSchedule.id,
          completed: true,
          minutes_spent: timerMinutes
        })
      })
        .then(res => res.json())
        .then(() => {
          fetchData();
        })
        .catch(err => console.error(err));
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  if (loading) {
    return <div style={{ color: 'var(--text-secondary)', padding: '2rem' }}>Loading your Spark Master Planner...</div>;
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
        <AlertCircle size={48} color="var(--error)" />
        <h3 style={{ fontSize: '1.25rem' }}>Error loading schedule</h3>
        <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
        <button className="btn btn-primary" onClick={fetchData}>Try Again</button>
      </div>
    );
  }

  const { schedules, total_points, weekly_points, weekly_target, milestone } = data;
  
  // Group schedules by category for the syllabus page
  const syllabus = {
    Beginner: schedules.filter(s => s.topic_category === 'Beginner'),
    Intermediate: schedules.filter(s => s.topic_category === 'Intermediate'),
    Master: schedules.filter(s => s.topic_category === 'Master')
  };

  const completedCount = schedules.filter(s => s.completed).length;
  const progressPercent = Math.round((completedCount / schedules.length) * 100);

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>⚡ Spark Master Path</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Code to System Design & Pipeline ETL Mastery</p>
        </div>
        <button 
          className="btn btn-secondary" 
          onClick={() => handleResetSchedule('2026-07-24')}
          style={{ fontSize: '0.85rem' }}
        >
          <RotateCcw size={14} /> Reset Schedule (July 24, 2026)
        </button>
      </div>

      {/* Progress Cards */}
      <div className="metric-grid" style={{ marginBottom: '2rem' }}>
        {/* Total Points Card */}
        <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--secondary)' }}>
          <div className="label">Total Points Earned</div>
          <div className="value" style={{ color: 'var(--secondary)', textShadow: '0 0 15px var(--secondary-glow)' }}>
            {total_points} PTS
          </div>
          <div className="subtext">10 points per completed topic</div>
        </div>

        {/* Weekly Target Card */}
        <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--primary)' }}>
          <div className="label">Weekly Goal Progress</div>
          <div className="value" style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
            {weekly_points} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>/ {weekly_target} PTS</span>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden', marginTop: '0.25rem' }}>
            <div style={{ height: '100%', background: 'var(--primary)', width: `${Math.min(100, (weekly_points / weekly_target) * 100)}%` }} />
          </div>
          <div className="subtext" style={{ marginTop: '0.25rem' }}>
            {weekly_points >= weekly_target ? '🎉 Weekly target achieved!' : `${weekly_target - weekly_points} pts left this week`}
          </div>
        </div>

        {/* Milestone Card */}
        <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--success)' }}>
          <div className="label">Current Milestone</div>
          <div className="value" style={{ fontSize: '1.5rem', color: 'var(--success)', marginTop: '0.25rem', whiteSpace: 'nowrap' }}>
            {milestone}
          </div>
          <div className="subtext" style={{ marginTop: '0.50rem' }}>
            Progress: {completedCount} / {schedules.length} Topics ({progressPercent}%)
          </div>
        </div>
      </div>

      {/* Main Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-glass)', marginBottom: '2rem', gap: '1.5rem' }}>
        <button 
          onClick={() => setActiveTab('schedule')} 
          style={{ 
            background: 'none', 
            border: 'none', 
            color: activeTab === 'schedule' ? 'var(--primary)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'schedule' ? '2px solid var(--primary)' : '2px solid transparent',
            padding: '0.75rem 0.5rem',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all var(--transition-fast)'
          }}
        >
          <Calendar size={18} /> Recommended Schedule
        </button>
        <button 
          onClick={() => setActiveTab('syllabus')} 
          style={{ 
            background: 'none', 
            border: 'none', 
            color: activeTab === 'syllabus' ? 'var(--primary)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'syllabus' ? '2px solid var(--primary)' : '2px solid transparent',
            padding: '0.75rem 0.5rem',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all var(--transition-fast)'
          }}
        >
          <BookOpen size={18} /> Spark Syllabus
        </button>
        <button 
          onClick={() => setActiveTab('timer')} 
          style={{ 
            background: 'none', 
            border: 'none', 
            color: activeTab === 'timer' ? 'var(--primary)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'timer' ? '2px solid var(--primary)' : '2px solid transparent',
            padding: '0.75rem 0.5rem',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all var(--transition-fast)'
          }}
        >
          <Clock size={18} /> Focus Timer
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2.5rem' }}>
        
        {/* Left Column: Tab contents */}
        <div>
          {activeTab === 'schedule' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', fontWeight: 600 }}>Daily Roadmap Timeline</h3>
              {schedules.map((item) => {
                const isSelected = selectedSchedule?.id === item.id;
                return (
                  <div 
                    key={item.id} 
                    className="glass-panel" 
                    style={{ 
                      padding: '1.25rem', 
                      borderLeft: isSelected ? '4px solid var(--primary)' : '4px solid transparent',
                      background: isSelected ? 'rgba(255, 75, 75, 0.02)' : 'var(--bg-card)',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'all var(--transition-fast)'
                    }}
                    onClick={() => setSelectedSchedule(item)}
                  >
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      <div onClick={(e) => { e.stopPropagation(); handleToggleComplete(item.id, item.completed); }} style={{ cursor: 'pointer' }}>
                        {item.completed ? (
                          <CheckCircle2 size={24} color="var(--success)" />
                        ) : (
                          <div style={{ width: '24px', height: '24px', borderRadius: '50%', border: '2px solid var(--text-muted)' }} />
                        )}
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.15rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.1rem 0.4rem', borderRadius: '4px', background: item.topic_category === 'Beginner' ? '#00e67622' : item.topic_category === 'Intermediate' ? '#00f2fe22' : '#ff4b4b22', color: item.topic_category === 'Beginner' ? 'var(--success)' : item.topic_category === 'Intermediate' ? 'var(--secondary)' : 'var(--primary)' }}>
                            {item.topic_category.toUpperCase()}
                          </span>
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                            📅 {item.scheduled_date}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: item.completed ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                          {item.topic_title}
                        </h4>
                      </div>
                    </div>
                    <ChevronRight size={20} color="var(--text-muted)" />
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'syllabus' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
              {Object.keys(syllabus).map(lvl => (
                <div key={lvl}>
                  <h3 style={{ fontSize: '1.35rem', fontWeight: 700, marginBottom: '1rem', color: lvl === 'Beginner' ? 'var(--success)' : lvl === 'Intermediate' ? 'var(--secondary)' : 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {lvl === 'Beginner' && <Star size={20} />}
                    {lvl === 'Intermediate' && <Award size={20} />}
                    {lvl === 'Master' && <Trophy size={20} />}
                    {lvl} Core Syllabus
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                    {syllabus[lvl].map(item => (
                      <div key={item.id} className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '0.75rem' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                            <h4 style={{ fontSize: '1.05rem', fontWeight: 600 }}>{item.topic_title}</h4>
                            {item.completed && <CheckCircle2 size={18} color="var(--success)" />}
                          </div>
                          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: '1.4' }}>
                            {item.topic_description}
                          </p>
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                          {item.topic_subtopics.map((sub, idx) => (
                            <span key={idx} className="badge badge-category" style={{ fontSize: '0.675rem', padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)' }}>
                              {sub}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'timer' && (
            <div className="glass-panel" style={{ padding: '3rem 2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>Custom Focus Session</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {selectedSchedule ? `Focusing on: ${selectedSchedule.topic_title}` : 'Select a topic from recommended schedule to link focus session'}
                </p>
              </div>

              {/* Timer Circle */}
              <div style={{ 
                width: '240px', 
                height: '240px', 
                borderRadius: '50%', 
                border: '8px solid var(--border-glass)', 
                borderTopColor: 'var(--primary)',
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'center', 
                alignItems: 'center',
                boxShadow: '0 0 30px var(--primary-glow)'
              }}>
                <span style={{ fontSize: '3.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {formatTime(timeLeft)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  minutes left
                </span>
              </div>

              {/* Custom Input */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 600 }}>Set Duration:</span>
                <input 
                  type="number" 
                  value={timerMinutes} 
                  onChange={(e) => handleCustomMinutesChange(e.target.value)}
                  style={{ 
                    width: '70px', 
                    padding: '0.5rem', 
                    borderRadius: '8px', 
                    background: 'rgba(0,0,0,0.2)', 
                    border: '1px solid var(--border-glass)', 
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '1rem',
                    textAlign: 'center'
                  }}
                  disabled={isTimerRunning}
                />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>mins</span>
              </div>

              {/* Controls */}
              <div style={{ display: 'flex', gap: '1.25rem' }}>
                {isTimerRunning ? (
                  <button className="btn btn-secondary" onClick={pauseTimer} style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--border-glass)' }}>
                    <Pause size={18} /> Pause
                  </button>
                ) : (
                  <button className="btn btn-primary" onClick={startTimer}>
                    <Play size={18} fill="currentColor" /> Start Focus
                  </button>
                )}
                <button className="btn btn-secondary" onClick={resetTimer} style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-secondary)', border: '1px solid var(--border-glass)' }}>
                  <RotateCcw size={18} /> Reset
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Selected Topic details / quick actions */}
        <div>
          {selectedSchedule ? (
            <div className="glass-panel" style={{ padding: '1.75rem', position: 'sticky', top: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px', background: selectedSchedule.topic_category === 'Beginner' ? '#00e67622' : selectedSchedule.topic_category === 'Intermediate' ? '#00f2fe22' : '#ff4b4b22', color: selectedSchedule.topic_category === 'Beginner' ? 'var(--success)' : selectedSchedule.topic_category === 'Intermediate' ? 'var(--secondary)' : 'var(--primary)' }}>
                  {selectedSchedule.topic_category.toUpperCase()}
                </span>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 700, marginTop: '0.75rem', marginBottom: '0.5rem' }}>
                  {selectedSchedule.topic_title}
                </h3>
                <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <span>📅 Date: <strong>{selectedSchedule.scheduled_date}</strong></span>
                  <span>💎 Points: <strong>{selectedSchedule.topic_points}</strong></span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.5rem' }}>Topic Overview</h4>
                <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-primary)' }}>
                  {selectedSchedule.topic_description}
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.75rem' }}>Key Concepts to Cover</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selectedSchedule.topic_subtopics.map((sub, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <Zap size={14} color="var(--warning)" />
                      <span>{sub}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <button 
                  className="btn btn-primary" 
                  onClick={() => {
                    setActiveTab('timer');
                    setTimeLeft(timerMinutes * 60);
                  }}
                  style={{ width: '100%' }}
                >
                  <Clock size={16} /> Start Focus Timer
                </button>
                <button 
                  className="btn btn-secondary" 
                  onClick={() => handleToggleComplete(selectedSchedule.id, selectedSchedule.completed)}
                  style={{ 
                    width: '100%', 
                    background: selectedSchedule.completed ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255,255,255,0.03)', 
                    color: selectedSchedule.completed ? 'var(--success)' : '#fff',
                    border: '1px solid var(--border-glass)' 
                  }}
                >
                  <CheckCircle2 size={16} /> {selectedSchedule.completed ? 'Completed' : 'Mark Completed'}
                </button>
              </div>
              
              {selectedSchedule.focus_minutes_spent > 0 && (
                <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  ⏱️ Focus duration logged: {selectedSchedule.focus_minutes_spent} minutes
                </div>
              )}
            </div>
          ) : (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a topic to view progress and details.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default SparkMasterPlanner;
