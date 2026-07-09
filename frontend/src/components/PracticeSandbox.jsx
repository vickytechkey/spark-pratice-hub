import React, { useEffect, useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Play, FileText, Database, Send, Terminal, Loader2, Sparkles } from 'lucide-react';

function PracticeSandbox({ problemId, onSelectProblem }) {
  const [problemsList, setProblemsList] = useState([]);
  const [currentProblemId, setCurrentProblemId] = useState(problemId || '');
  const [problemData, setProblemData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  
  // Tabs
  const [activeLeftTab, setActiveLeftTab] = useState('description');
  
  // Spark Profiles
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('Interview');
  
  // Code editor code
  const [code, setCode] = useState('');
  
  // Run Results
  const [runResult, setRunResult] = useState(null);

  useEffect(() => {
    // Fetch all problems for select switch dropdown
    fetch('http://localhost:8000/api/problems/')
      .then(res => res.json())
      .then(data => {
        setProblemsList(data);
        if (data.length > 0 && !currentProblemId) {
          setCurrentProblemId(data[0].id);
        }
      });
      
    // Fetch profiles
    fetch('http://localhost:8000/api/profiles/')
      .then(res => res.json())
      .then(data => {
        setProfiles(data);
        if (data.length > 0) {
          setSelectedProfile(data[0].name);
        }
      });
  }, []);

  useEffect(() => {
    if (currentProblemId) {
      fetchProblemDetails(currentProblemId);
      // reset run result
      setRunResult(null);
    }
  }, [currentProblemId]);

  const fetchProblemDetails = (id) => {
    setLoading(true);
    fetch(`http://localhost:8000/api/problems/${id}/details/`)
      .then(res => res.json())
      .then(data => {
        setProblemData(data);
        // Autofill default code template based on inputs
        const firstTc = data.inputs_preview || {};
        const inputKeys = Object.keys(firstTc);
        const inputParams = inputKeys.length > 0 ? inputKeys.join(', ') : 'inputs';
        
        // Check if there is already a successful submission code to restore
        fetch('http://localhost:8000/api/submissions/')
          .then(r => r.json())
          .then(subs => {
            const lastSub = subs.find(s => s.problem === id);
            if (lastSub) {
              setCode(lastSub.code);
            } else {
              // Pre-fill template
              setCode(`def solve(spark, inputs):
    # inputs is a dictionary of name: DataFrame
    # Let's extract inputs:
${inputKeys.map(k => `    ${k} = inputs['${k}']`).join('\n')}
    
    # Write your PySpark code here
    
    return ${inputKeys[0] || 'df'}
`);
            }
          });
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleRunCode = (submit = true) => {
    setRunning(true);
    setRunResult(null);
    fetch('http://localhost:8000/api/practice/run/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        problem_id: currentProblemId,
        code: code,
        profile_name: selectedProfile,
        submit: submit
      })
    })
      .then(res => res.json())
      .then(data => {
        setRunResult(data);
        setRunning(false);
      })
      .catch(err => {
        console.error(err);
        setRunning(false);
      });
  };

  if (loading || !problemData) {
    return <div style={{ color: 'var(--text-secondary)' }}>Loading Practice Sandbox environment...</div>;
  }

  const { problem, inputs_preview, expected_preview } = problemData;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 5rem)' }}>
      
      {/* Header bar */}
      <div style={{ display: 'flex', justifycontent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <select 
            value={currentProblemId} 
            onChange={(e) => {
              setCurrentProblemId(e.target.value);
              if (onSelectProblem) onSelectProblem(e.target.value);
            }}
            style={{
              padding: '0.625rem 1.25rem',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontWeight: 600,
              outline: 'none',
              fontSize: '1rem'
            }}
          >
            {problemsList.map(p => (
              <option key={p.id} value={p.id}>{p.id} - {p.title}</option>
            ))}
          </select>
          
          <span className={`badge badge-${problem.difficulty.toLowerCase()}`}>
            {problem.difficulty}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{problem.category}</span>
        </div>

        {/* Profile and Run buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Profile:</span>
            <select 
              value={selectedProfile}
              onChange={(e) => setSelectedProfile(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-glass)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                outline: 'none',
                fontSize: '0.875rem'
              }}
            >
              {profiles.map(p => (
                <option key={p.name} value={p.name}>{p.name}</option>
              ))}
            </select>
          </div>
          
          <button 
            className="btn btn-secondary"
            onClick={() => handleRunCode(false)}
            disabled={running}
            style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Run Code
          </button>

          <button 
            className="btn btn-primary"
            onClick={() => handleRunCode(true)}
            disabled={running}
            style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
          >
            {running ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Submit Code
          </button>
        </div>
      </div>

      {/* Main split Editor Pane */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '1.5rem', flex: 1, minHeight: 0 }}>
        
        {/* Left Side: Tabs */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          
          {/* Tabs bar */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.01)' }}>
            <div 
              style={{ 
                padding: '0.875rem 1.25rem', 
                borderBottom: activeLeftTab === 'description' ? '2px solid var(--primary)' : 'none',
                color: activeLeftTab === 'description' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.875rem'
              }}
              onClick={() => setActiveLeftTab('description')}
            >
              Description
            </div>
            <div 
              style={{ 
                padding: '0.875rem 1.25rem', 
                borderBottom: activeLeftTab === 'inputs' ? '2px solid var(--primary)' : 'none',
                color: activeLeftTab === 'inputs' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.875rem'
              }}
              onClick={() => setActiveLeftTab('inputs')}
            >
              Input Datasets
            </div>
            <div 
              style={{ 
                padding: '0.875rem 1.25rem', 
                borderBottom: activeLeftTab === 'expected' ? '2px solid var(--primary)' : 'none',
                color: activeLeftTab === 'expected' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.875rem'
              }}
              onClick={() => setActiveLeftTab('expected')}
            >
              Expected Output
            </div>
          </div>

          {/* Left Tab content area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
            {activeLeftTab === 'description' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 700 }}>{problem.title}</h3>
                <p style={{ lineHeight: '1.6', color: 'var(--text-primary)' }}>
                  {problem.description}
                </p>
                
                {problem.companies && problem.companies.length > 0 && (
                  <div>
                    <h5 style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>COMPANIES</h5>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {problem.companies.map((c, idx) => (
                        <span key={idx} style={{ background: 'rgba(255, 75, 75, 0.1)', color: 'var(--primary)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600 }}>
                          {c.company} ({c.frequency})
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {problem.concepts && (
                  <div>
                    <h5 style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>CONCEPTS</h5>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {problem.concepts.split(',').map(c => (
                        <span key={c} style={{ background: 'rgba(255,255,255,0.04)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                          {c.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {problem.hints && (
                  <div style={{ background: 'rgba(255, 179, 0, 0.05)', border: '1px solid rgba(255, 179, 0, 0.1)', padding: '1rem', borderRadius: '8px' }}>
                    <h5 style={{ color: 'var(--warning)', fontWeight: 600, marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Sparkles size={16} /> Hint
                    </h5>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                      {problem.hints}
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeLeftTab === 'inputs' && (
              <div>
                {Object.keys(inputs_preview).map(key => (
                  <div key={key} style={{ marginBottom: '1.5rem' }}>
                    <h4 style={{ fontWeight: 600, marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.95rem' }}>
                      DataFrame: `{key}`
                    </h4>
                    <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-glass)', borderRadius: '8px' }}>
                      <table className="custom-table" style={{ fontSize: '0.85rem' }}>
                        <thead>
                          <tr>
                            {inputs_preview[key].length > 0 && Object.keys(inputs_preview[key][0]).map(col => (
                              <th key={col}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {inputs_preview[key].map((row, rIdx) => (
                            <tr key={rIdx}>
                              {Object.values(row).map((val, cIdx) => (
                                <td key={cIdx}>{val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeLeftTab === 'expected' && (
              <div>
                <h4 style={{ fontWeight: 600, marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', fontSize: '0.95rem' }}>
                  Expected Schema & Content preview
                </h4>
                <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-glass)', borderRadius: '8px' }}>
                  <table className="custom-table" style={{ fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        {expected_preview.length > 0 && Object.keys(expected_preview[0]).map(col => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {expected_preview.map((row, rIdx) => (
                        <tr key={rIdx}>
                          {Object.values(row).map((val, cIdx) => (
                            <td key={cIdx}>{val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Monaco Editor + Console logs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: 0 }}>
          
          {/* Monaco Editor Panel */}
          <div className="glass-panel" style={{ flex: 1.3, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem 0' }}>
            <Editor
              height="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                fontSize: 14,
                fontFamily: 'var(--font-mono)',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                automaticLayout: true
              }}
            />
          </div>

          {/* Console Output Console */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.01)', flexShrink: 0 }}>
              <Terminal size={16} color="var(--primary)" />
              <h4 style={{ fontSize: '0.875rem', fontWeight: 600 }}>Test Runner Results</h4>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
              {runResult ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>Status:</span>
                      <span style={{ 
                        color: runResult.status === 'PASS' ? 'var(--success)' : 'var(--error)', 
                        fontWeight: 700 
                      }}>
                        {runResult.status}
                      </span>
                    </div>
                    {runResult.total_time_ms && (
                      <span style={{ color: 'var(--text-muted)' }}>Time: {runResult.total_time_ms} ms</span>
                    )}
                  </div>
                  
                  {runResult.results && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {runResult.results.map((tc, idx) => (
                        <div key={idx} style={{ 
                          padding: '0.75rem', 
                          borderRadius: '6px', 
                          background: tc.passed ? 'rgba(0, 230, 118, 0.05)' : 'rgba(255, 23, 68, 0.05)',
                          border: tc.passed ? '1px solid rgba(0, 230, 118, 0.15)' : '1px solid rgba(255, 23, 68, 0.15)'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ fontWeight: 600 }}>Test Case {idx + 1}</span>
                            <span style={{ color: tc.passed ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
                              {tc.passed ? 'Passed' : 'Failed'}
                            </span>
                          </div>
                          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{tc.message}</p>
                          
                          {/* If there is captured stdout (print statements): show it */}
                          {tc.captured_output && (
                            <div style={{ marginTop: '0.5rem' }}>
                              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Console Output</div>
                              <pre style={{ background: '#000', color: '#00ff66', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', overflowX: 'auto', margin: 0, fontFamily: 'var(--font-mono)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                {tc.captured_output}
                              </pre>
                            </div>
                          )}

                          {/* If failed and preview is available: show actual vs expected */}
                          {!tc.passed && tc.actual_preview && tc.actual_preview.length > 0 && (
                            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', minWidth: 0 }}>
                                <div style={{ minWidth: 0 }}>
                                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--error)', marginBottom: '0.25rem' }}>Actual Output (First 10 rows)</div>
                                  <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,23,68,0.2)', borderRadius: '6px' }}>
                                    <table className="custom-table" style={{ fontSize: '0.75rem', margin: 0 }}>
                                      <thead>
                                        <tr>
                                          {Object.keys(tc.actual_preview[0]).map(col => (
                                            <th key={col} style={{ padding: '0.5rem' }}>{col}</th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {tc.actual_preview.map((row, rIdx) => (
                                          <tr key={rIdx}>
                                            {Object.values(row).map((val, cIdx) => (
                                              <td key={cIdx} style={{ padding: '0.5rem' }}>{val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</td>
                                            ))}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                                
                                <div style={{ minWidth: 0 }}>
                                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)', marginBottom: '0.25rem' }}>Expected Output (First 10 rows)</div>
                                  <div style={{ overflowX: 'auto', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(0,230,118,0.2)', borderRadius: '6px' }}>
                                    <table className="custom-table" style={{ fontSize: '0.75rem', margin: 0 }}>
                                      <thead>
                                        <tr>
                                          {tc.expected_preview && tc.expected_preview.length > 0 && Object.keys(tc.expected_preview[0]).map(col => (
                                            <th key={col} style={{ padding: '0.5rem' }}>{col}</th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {tc.expected_preview && tc.expected_preview.map((row, rIdx) => (
                                          <tr key={rIdx}>
                                            {Object.values(row).map((val, cIdx) => (
                                              <td key={cIdx} style={{ padding: '0.5rem' }}>{val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val)}</td>
                                            ))}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* If error: show traceback */}
                          {tc.traceback && (
                            <pre style={{ background: '#000', color: 'var(--error)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', marginTop: '0.5rem', overflowX: 'auto' }}>
                              {tc.traceback}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {runResult.status === 'ERROR' && (
                    <div style={{ color: 'var(--error)' }}>
                      <p>{runResult.message}</p>
                      {runResult.traceback && (
                        <pre style={{ background: '#000', color: 'var(--error)', padding: '0.5rem', borderRadius: '4px', fontSize: '0.75rem', marginTop: '0.5rem', overflowX: 'auto' }}>
                          {runResult.traceback}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '2rem' }}>
                  {running ? 'Running user solution against 10 test cases in PySpark...' : 'Click "Run PySpark" to validate solution.'}
                </div>
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

export default PracticeSandbox;
