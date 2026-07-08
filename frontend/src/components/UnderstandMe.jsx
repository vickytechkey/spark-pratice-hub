import React, { useEffect, useState } from 'react';
import { BookOpen, FileCode, Download, Table, HelpCircle, Archive } from 'lucide-react';

function UnderstandMe() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = () => {
    fetch('http://localhost:8000/api/submissions/')
      .then(res => res.json())
      .then(data => {
        setHistory(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleExport = (format) => {
    window.open(`http://localhost:8000/api/export/?format=${format}`, '_blank');
  };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Understand Me</h1>
        <p style={{ color: 'var(--text-secondary)' }}>F.A.Qs, user documentation, and practice history export tool</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2rem' }}>
        
        {/* Left pane: FAQs and Help */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <HelpCircle size={20} color="var(--primary)" /> Frequently Asked Questions
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <h5 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>How does correct output validation work?</h5>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  The runner compares user-returned DataFrames against target expected outputs in three comparison modes: <b>Exact</b> (matches schemas, sorted row ordering, and row content), <b>Ignore row order</b> (compares elements ignoring rows ordering), and <b>Schema only</b> or <b>Row count</b>.
                </p>
              </div>

              <div>
                <h5 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>How is the execution environment configured?</h5>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  Execution utilizes local PySpark sessions built dynamically based on resource profiles under "Spark Profiles". Changing profiles updates Spark configurations (cores, shuffle partitions, and memory limit).
                </p>
              </div>

              <div>
                <h5 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Where are the imported datasets stored?</h5>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  All imported problems Excel datasets get extracted and saved locally inside the <code>datasets/</code> folder, registering metadata paths inside SQLite.
                </p>
              </div>
            </div>
          </div>

          {/* Export Panel */}
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Download size={20} color="var(--secondary)" /> Export Practice History
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: '1.5' }}>
              Export all code submissions and metrics history into raw data formats.
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <button className="btn btn-secondary" onClick={() => handleExport('csv')} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem' }}>
                <Table size={20} color="var(--success)" />
                <span>Export CSV</span>
              </button>
              <button className="btn btn-secondary" onClick={() => handleExport('excel')} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem' }}>
                <Table size={20} color="var(--secondary)" />
                <span>Export Excel</span>
              </button>
              <button className="btn btn-secondary" onClick={() => handleExport('zip')} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '1rem' }}>
                <Archive size={20} color="var(--primary)" />
                <span>Export Code ZIP</span>
              </button>
            </div>
          </div>

        </div>

        {/* Right pane: Submissions History */}
        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', overflow: 'hidden', height: 'fit-content' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileCode size={20} color="var(--primary)" /> Recent Submissions
          </h3>

          {loading ? (
            <div style={{ color: 'var(--text-secondary)' }}>Loading submissions...</div>
          ) : history.length === 0 ? (
            <div style={{ color: 'var(--text-muted)' }}>No submissions found yet. Start solving problems to build history!</div>
          ) : (
            <div style={{ overflowY: 'auto', maxHeight: '400px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {history.slice(0, 20).map((sub) => (
                <div key={sub.id} style={{ padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-glass)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sub.problem_title}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {sub.problem} • {new Date(sub.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <span style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 700, 
                    color: sub.status === 'PASS' ? 'var(--success)' : 'var(--error)' 
                  }}>
                    {sub.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default UnderstandMe;
