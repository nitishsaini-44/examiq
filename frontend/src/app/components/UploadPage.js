'use client';
import { useState, useCallback } from 'react';
import { uploadPapers, runAnalysis } from '../../lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function UploadPage({ onAnalysisComplete }) {
  const [papers, setPapers] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [examDays, setExamDays] = useState(30);
  const [hoursPerDay, setHoursPerDay] = useState(6);
  const [subject, setSubject] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    const files = Array.from(e.dataTransfer.files).filter(f =>
      /\.(pdf|png|jpg|jpeg|docx|doc|txt)$/i.test(f.name)
    );
    setPapers(prev => [...prev, ...files]);
  }, []);

  const handlePaperSelect = (e) => {
    const files = Array.from(e.target.files);
    setPapers(prev => [...prev, ...files]);
  };

  const handleUpload = async () => {
    if (papers.length === 0) { setError('Please select at least one paper'); return; }
    setUploading(true);
    setError('');
    try {
      const result = await uploadPapers(papers);
      setUploadResult(result);

    } catch (err) {
      setError('Upload failed: ' + err.message);
    }
    setUploading(false);
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const result = await runAnalysis({ exam_days: examDays, hours_per_day: hoursPerDay, subject: subject || 'General' });
      if (result.success) {
        onAnalysisComplete(result.result);
      } else {
        setError(result.message || 'Analysis failed');
      }
    } catch (err) {
      setError('Analysis failed: ' + err.message);
    }
    setAnalyzing(false);
  };



  if (analyzing) {
    return (
      <div className="loading-overlay animate-fade">
        <div className="spinner" />
        <div className="loading-text">🧠 AI is analyzing your papers...</div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: 400, textAlign: 'center' }}>
          Extracting questions, computing embeddings, clustering topics, scoring importance, generating predictions and study plan...
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade">
      <div className="hero">
        <h1 className="hero-title">ExamIQ</h1>
        <p className="hero-subtitle">Transform past exam papers into an AI-powered study strategy. Upload your papers and let our engine do the heavy lifting.</p>
      </div>

      {error && <div className="alert-card alert-fire" style={{ marginBottom: 24 }}>⚠️ {error}</div>}

      <div className="grid-2" style={{ maxWidth: 1000, margin: '0 auto' }}>
        {/* Papers Upload */}
        <div className="card animate-slide">
          <div className="card-header">
            <div className="card-title">📄 Past Papers</div>
            <span className="card-subtitle">{papers.length} file(s)</span>
          </div>
          <div
            className={`upload-zone ${dragActive ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('paper-input').click()}
          >
            <div className="upload-icon">📂</div>
            <div className="upload-title">Drop papers here</div>
            <div className="upload-subtitle">PDF, DOCX, DOC, TXT, PNG, JPG • Multiple files supported</div>
            <input id="paper-input" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.docx,.doc,.txt" onChange={handlePaperSelect} style={{ display: 'none' }} />
          </div>
          {papers.length > 0 && (
            <div style={{ marginTop: 16, maxHeight: 150, overflow: 'auto' }}>
              {papers.map((f, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 8, marginBottom: 4, fontSize: 13 }}>
                  <span>{f.name}</span>
                  <button onClick={() => setPapers(prev => prev.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', fontSize: 16 }}>×</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card animate-slide" style={{ animationDelay: '0.1s' }}>
          <div className="card-header">
            <div className="card-title">⚙️ Settings</div>
            <span className="card-subtitle">Optional</span>
          </div>

          {/* Settings */}
          <div style={{ marginTop: 20 }}>
            <label style={{ fontSize: 13, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Subject Name</label>
            <input value={subject} onChange={e => setSubject(e.target.value)} placeholder="e.g. Data Structures" style={{ width: '100%', padding: '10px 14px', background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-sans)', outline: 'none' }} />
            <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Days to Exam</label>
                <input type="number" value={examDays} onChange={e => setExamDays(+e.target.value)} min={1} max={365} style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-sans)', outline: 'none' }} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Hours/Day</label>
                <input type="number" value={hoursPerDay} onChange={e => setHoursPerDay(+e.target.value)} min={1} max={16} style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 14, fontFamily: 'var(--font-sans)', outline: 'none' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ textAlign: 'center', marginTop: 32 }}>
        {!uploadResult ? (
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || papers.length === 0}>
            {uploading ? '⏳ Uploading...' : '📤 Upload Files'}
          </button>
        ) : (
          <div className="animate-fade">
            <div className="alert-card alert-success" style={{ maxWidth: 500, margin: '0 auto 20px', justifyContent: 'center' }}>
              ✅ {uploadResult.message} {uploadResult.years_detected?.length > 0 && `• Years: ${uploadResult.years_detected.join(', ')}`}
            </div>
            <button className="btn btn-primary" onClick={handleAnalyze} style={{ fontSize: 16, padding: '14px 36px' }}>
              🚀 Analyze with AI
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
