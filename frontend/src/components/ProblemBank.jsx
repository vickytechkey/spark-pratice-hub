import React, { useEffect, useState } from 'react';
import { Search, Database, ChevronLeft, ChevronRight, Check } from 'lucide-react';

function ProblemBank({ onSelectProblem }) {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filter States
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('All');
  const [category, setCategory] = useState('All');
  const [status, setStatus] = useState('All');
  
  // Pagination States
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchProblems();
  }, [search, difficulty, category, status]);

  const fetchProblems = () => {
    setLoading(true);
    const params = new URLSearchParams({
      search: search,
      difficulty: difficulty,
      category: category,
      status: status
    });
    
    fetch(`http://localhost:8000/api/problems/?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
        setProblems(data);
        setLoading(false);
        setCurrentPage(1); // reset to page 1 on filter change
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  const categories = [
    "All",
    "Filtering & Sorting",
    "Date & String",
    "Aggregations",
    "Joins",
    "Advanced Nested & Pivot",
    "Window Functions",
    "Data Cleaning & Null Handling",
    "Performance & Optimization",
    "Array & Map Operations",
    "User Defined Functions (UDFs)"
  ];

  // Pagination math
  const totalItems = problems.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedProblems = problems.slice(startIndex, startIndex + pageSize);

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Problem Bank</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Browse and search PySpark coding judge problems</p>
      </div>

      {/* Filters Container */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        
        {/* Search */}
        <div style={{ flex: 2, minWidth: '240px', position: 'relative' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text" 
            placeholder="Search problems, concepts..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '0.625rem 1rem 0.625rem 2.5rem', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-glass)', 
              borderRadius: '8px', 
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
        </div>

        {/* Difficulty */}
        <div style={{ flex: 1, minWidth: '120px' }}>
          <select 
            value={difficulty} 
            onChange={(e) => setDifficulty(e.target.value)}
            style={{
              width: '100%', 
              padding: '0.625rem 1rem', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-glass)', 
              borderRadius: '8px', 
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          >
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>

        {/* Category */}
        <div style={{ flex: 1.5, minWidth: '180px' }}>
          <select 
            value={category} 
            onChange={(e) => setCategory(e.target.value)}
            style={{
              width: '100%', 
              padding: '0.625rem 1rem', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-glass)', 
              borderRadius: '8px', 
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          >
            <option value="All">All Categories</option>
            {categories.filter(c => c !== 'All').map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {/* Status */}
        <div style={{ flex: 1, minWidth: '120px' }}>
          <select 
            value={status} 
            onChange={(e) => setStatus(e.target.value)}
            style={{
              width: '100%', 
              padding: '0.625rem 1rem', 
              background: 'rgba(255,255,255,0.03)', 
              border: '1px solid var(--border-glass)', 
              borderRadius: '8px', 
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          >
            <option value="All">All Status</option>
            <option value="Completed">Completed</option>
            <option value="Pending">Pending</option>
          </select>
        </div>
      </div>

      {/* Problems List */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading problems...</div>
        ) : problems.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No problems found matching criteria.</div>
        ) : (
          <div>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Status</th>
                  <th style={{ width: '120px' }}>ID</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th style={{ width: '120px' }}>Difficulty</th>
                  <th style={{ width: '100px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {paginatedProblems.map((prob) => (
                  <tr key={prob.id}>
                    <td>
                      {prob.is_solved ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '22px', height: '22px', borderRadius: '50%', background: 'rgba(0, 230, 118, 0.1)', color: '#00e676' }}>
                          <Check size={14} />
                        </div>
                      ) : (
                        <div style={{ width: '22px', height: '22px', borderRadius: '50%', border: '2px dashed var(--text-muted)' }} />
                      )}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{prob.id}</td>
                    <td style={{ fontWeight: 600 }}>
                      <div>{prob.title}</div>
                      {prob.companies && prob.companies.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginTop: '0.25rem' }}>
                          {prob.companies.slice(0, 3).map((c, idx) => (
                            <span 
                              key={idx} 
                              style={{ 
                                fontSize: '0.65rem', 
                                background: 'rgba(255,255,255,0.05)', 
                                padding: '0.1rem 0.35rem', 
                                borderRadius: '4px', 
                                color: 'var(--text-muted)' 
                              }}
                              title={c.frequency}
                            >
                              {c.company}
                            </span>
                          ))}
                          {prob.companies.length > 3 && (
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>+{prob.companies.length - 3}</span>
                          )}
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{prob.category}</td>
                    <td>
                      <span className={`badge badge-${prob.difficulty.toLowerCase()}`}>
                        {prob.difficulty}
                      </span>
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary" 
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }}
                        onClick={() => onSelectProblem(prob.id)}
                      >
                        Solve
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderTop: '1px solid var(--border-glass)' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Showing {startIndex + 1} - {Math.min(startIndex + pageSize, totalItems)} of {totalItems} problems
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {/* Page limit selector */}
                <select 
                  value={pageSize}
                  onChange={(e) => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}
                  style={{
                    padding: '0.375rem 0.75rem',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '6px',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    fontSize: '0.875rem'
                  }}
                >
                  <option value={5}>5 / page</option>
                  <option value={10}>10 / page</option>
                  <option value={20}>20 / page</option>
                  <option value={50}>50 / page</option>
                </select>

                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button 
                    className="btn btn-secondary"
                    style={{ padding: '0.375rem', minWidth: '32px' }}
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(prev => prev - 1)}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span style={{ display: 'inline-flex', alignItems: 'center', padding: '0 0.75rem', fontSize: '0.875rem' }}>
                    Page {currentPage} of {totalPages}
                  </span>
                  <button 
                    className="btn btn-secondary"
                    style={{ padding: '0.375rem', minWidth: '32px' }}
                    disabled={currentPage === totalPages}
                    onClick={() => setCurrentPage(prev => prev + 1)}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProblemBank;
