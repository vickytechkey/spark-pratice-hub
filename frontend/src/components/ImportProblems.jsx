import React, { useState } from 'react';
import { Upload, FileSpreadsheet, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

function ImportProblems() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [isError, setIsError] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatusMsg(null);
  };

  const handleUpload = () => {
    if (!file) return;

    setUploading(true);
    setStatusMsg(null);
    setIsError(false);

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:8000/api/admin/import/', {
      method: 'POST',
      body: formData
    })
      .then(res => res.json().then(data => ({ status: res.status, body: data })))
      .then(({ status, body }) => {
        setUploading(false);
        if (status === 200) {
          setStatusMsg(body.message);
          setFile(null);
        } else {
          setIsError(true);
          setStatusMsg(body.error || 'Failed to import problems from Excel.');
        }
      })
      .catch(err => {
        console.error(err);
        setUploading(false);
        setIsError(true);
        setStatusMsg('Network connection error. Check backend console logs.');
      });
  };

  return (
    <div>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 700, marginBottom: '0.25rem' }}>Import Problems</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Upload an Excel workbook containing Problems, TestCases, and Datasets sheets</p>
      </div>

      <div className="glass-panel" style={{ padding: '2.5rem', maxWidth: '600px', textAlign: 'center' }}>
        <div style={{ margin: '0 auto 1.5rem', width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justify: 'center', color: 'var(--primary)' }}>
          <FileSpreadsheet size={32} />
        </div>
        
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>Select Excel Workbook</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '2rem', lineHeight: '1.5' }}>
          Ensure sheet structure matches:<br />
          - <code>Problems</code> (id, title, difficulty, category, description, concepts, hints, comparison_mode)<br />
          - <code>TestCases</code> (problem_id, input_datasets, expected_output_dataset, comparison_mode)<br />
          - <code>Datasets</code> (name, type, data)
        </p>

        {/* Drag and drop file field */}
        <div style={{ border: '2px dashed var(--border-glass)', borderRadius: '10px', padding: '2rem', position: 'relative', cursor: 'pointer', marginBottom: '1.5rem' }}>
          <input 
            type="file" 
            accept=".xlsx, .xls"
            onChange={handleFileChange}
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
          />
          <Upload size={24} color="var(--text-muted)" style={{ marginBottom: '0.5rem' }} />
          <div style={{ fontSize: '0.875rem', color: file ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: file ? 600 : 400 }}>
            {file ? file.name : 'Click or drag Excel file here'}
          </div>
        </div>

        {statusMsg && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.75rem',
            padding: '0.75rem 1rem', 
            borderRadius: '6px', 
            background: isError ? 'rgba(255, 23, 68, 0.05)' : 'rgba(0, 230, 118, 0.05)',
            border: isError ? '1px solid rgba(255, 23, 68, 0.15)' : '1px solid rgba(0, 230, 118, 0.15)',
            marginBottom: '1.5rem',
            textAlign: 'left',
            fontSize: '0.875rem'
          }}>
            {isError ? <AlertCircle size={18} color="var(--error)" /> : <CheckCircle2 size={18} color="var(--success)" />}
            <span style={{ color: isError ? 'var(--error)' : 'var(--success)' }}>{statusMsg}</span>
          </div>
        )}

        <button 
          className="btn btn-primary"
          style={{ width: '100%' }}
          disabled={!file || uploading}
          onClick={handleUpload}
        >
          {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
          {uploading ? 'Importing Problems...' : 'Upload Excel'}
        </button>

      </div>
    </div>
  );
}

export default ImportProblems;
