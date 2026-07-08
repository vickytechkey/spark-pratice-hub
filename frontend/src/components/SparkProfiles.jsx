import React, { useEffect, useState } from 'react';
import { Settings, Plus, Edit2, Trash2, Save, X } from 'lucide-react';

function SparkProfiles() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Editor Form States
  const [isEditing, setIsEditing] = useState(false);
  const [currentProfile, setCurrentProfile] = useState(null);
  
  const defaultFormState = {
    name: '',
    master: 'local[*]',
    driver_memory: '1g',
    executor_memory: '1g',
    executor_cores: 1,
    shuffle_partitions: 2,
    adaptive_query_execution: true,
    broadcast_threshold: 10485760,
    serializer: 'org.apache.spark.serializer.KryoSerializer',
    default_parallelism: 2,
    extra_configs: {}
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = () => {
    setLoading(true);
    fetch('http://localhost:8000/api/profiles/')
      .then(res => res.json())
      .then(data => {
        setProfiles(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleEditClick = (profile) => {
    setCurrentProfile({ ...profile });
    setIsEditing(true);
  };

  const handleCreateClick = () => {
    setCurrentProfile({ ...defaultFormState });
    setIsEditing(true);
  };

  const handleSave = () => {
    const isNew = !profiles.find(p => p.name === currentProfile.name);
    const url = isNew 
      ? 'http://localhost:8000/api/profiles/' 
      : `http://localhost:8000/api/profiles/${currentProfile.name}/`;
    const method = isNew ? 'POST' : 'PUT';

    fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(currentProfile)
    })
      .then(res => {
        if (res.ok) {
          setIsEditing(false);
          fetchProfiles();
        } else {
          alert('Error saving profile. Please check parameters.');
        }
      });
  };

  const handleDelete = (name) => {
    if (window.confirm(`Are you sure you want to delete profile "${name}"?`)) {
      fetch(`http://localhost:8000/api/profiles/${name}/`, {
        method: 'DELETE'
      })
        .then(() => {
          fetchProfiles();
        });
    }
  };

  const handleFormChange = (key, val) => {
    setCurrentProfile(prev => ({
      ...prev,
      [key]: val
    }));
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Spark Profiles</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Configure resource limits and engine settings for Spark session context</p>
        </div>
        
        {!isEditing && (
          <button className="btn btn-primary" onClick={handleCreateClick}>
            <Plus size={16} /> New Profile
          </button>
        )}
      </div>

      {isEditing ? (
        /* Edit Form */
        <div className="glass-panel" style={{ padding: '2rem', maxWidth: '800px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings size={20} color="var(--primary)" />
            {currentProfile.name ? `Edit Profile: ${currentProfile.name}` : 'Create New Profile'}
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            
            {/* Name */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Profile Name
              </label>
              <input 
                type="text" 
                value={currentProfile.name}
                disabled={profiles.find(p => p.name === currentProfile.name)}
                onChange={(e) => handleFormChange('name', e.target.value)}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>

            {/* Master URL */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Master URL
              </label>
              <input 
                type="text" 
                value={currentProfile.master}
                onChange={(e) => handleFormChange('master', e.target.value)}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>

            {/* Driver Memory */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Driver Memory (e.g., 1g, 2g)
              </label>
              <input 
                type="text" 
                value={currentProfile.driver_memory}
                onChange={(e) => handleFormChange('driver_memory', e.target.value)}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>

            {/* Executor Memory */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Executor Memory
              </label>
              <input 
                type="text" 
                value={currentProfile.executor_memory}
                onChange={(e) => handleFormChange('executor_memory', e.target.value)}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>

            {/* Executor Cores */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Executor Cores
              </label>
              <input 
                type="number" 
                value={currentProfile.executor_cores}
                onChange={(e) => handleFormChange('executor_cores', Number(e.target.value))}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>

            {/* Shuffle Partitions */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>
                Shuffle Partitions
              </label>
              <input 
                type="number" 
                value={currentProfile.shuffle_partitions}
                onChange={(e) => handleFormChange('shuffle_partitions', Number(e.target.value))}
                style={{ width: '100%', padding: '0.625rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: 'var(--text-primary)', outline: 'none' }}
              />
            </div>
            
            {/* AQE Switch */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1.5rem' }}>
              <input 
                type="checkbox" 
                checked={currentProfile.adaptive_query_execution}
                onChange={(e) => handleFormChange('adaptive_query_execution', e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                Enable Adaptive Query Execution (AQE)
              </label>
            </div>

          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={() => setIsEditing(false)}>
              <X size={16} /> Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave}>
              <Save size={16} /> Save Settings
            </button>
          </div>
        </div>
      ) : (
        /* Profiles list table */
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Profile Name</th>
                <th>Master URL</th>
                <th>Driver Memory</th>
                <th>Executor Memory</th>
                <th>Cores</th>
                <th>Partitions</th>
                <th style={{ width: '120px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.name}>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{p.master}</td>
                  <td>{p.driver_memory}</td>
                  <td>{p.executor_memory}</td>
                  <td>{p.executor_cores}</td>
                  <td>{p.shuffle_partitions}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem' }} onClick={() => handleEditClick(p)}>
                        <Edit2 size={14} />
                      </button>
                      <button className="btn btn-secondary" style={{ padding: '0.4rem', color: 'var(--error)' }} onClick={() => handleDelete(p.name)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SparkProfiles;
