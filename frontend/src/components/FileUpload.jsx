import { useRef, useState } from 'react';
import { FiUploadCloud, FiBarChart2, FiMessageSquare, FiTrendingUp, FiShield, FiZap } from 'react-icons/fi';
import './FileUpload.css';

function FileUpload({ onUpload, isUploading }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  const features = [
    { icon: <FiBarChart2 />, label: 'Smart Charts' },
    { icon: <FiMessageSquare />, label: 'AI Chat' },
    { icon: <FiTrendingUp />, label: 'Forecasting' },
    { icon: <FiShield />, label: 'Data Cleaning' },
    { icon: <FiZap />, label: 'Instant Insights' },
  ];

  return (
    <div className="upload-wrapper">
      {/* Hero Text */}
      <div className="hero-section">
        <div className="hero-badge">
          <span className="badge-dot" />
          AI-Powered Data Intelligence
        </div>

        <h1 className="hero-title">
          The <span className="grad">Smartest</span><br />
          way to understand<br />your data.
        </h1>

        <p className="hero-subtitle">
          DataPilot transforms raw CSV files into interactive insights,
          automated visualizations, and intelligent forecasts — powered by AI.
        </p>

        <div className="feature-pills">
          {features.map((f, i) => (
            <div key={i} className="feature-pill" style={{ animationDelay: `${i * 0.08}s` }}>
              <span className="pill-icon">{f.icon}</span>
              {f.label}
            </div>
          ))}
        </div>
      </div>

      {/* Upload Zone */}
      <div className="upload-zone-container">
        {/* Orbital rings */}
        {!isUploading && (
          <>
            <div className="orbit-ring orbit-ring-1">
              <div className="orbit-dot" />
            </div>
            <div className="orbit-ring orbit-ring-2">
              <div className="orbit-dot" />
            </div>
          </>
        )}

        <div
          className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !isUploading && fileInputRef.current.click()}
          id="file-drop-zone"
          role="button"
          aria-label="Upload CSV file"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current.click()}
        >
          {isUploading ? (
            <div className="upload-loading">
              <div className="upload-loading-ring" />
              <p className="upload-loading-text">Processing your data...</p>
              <p className="upload-loading-sub">Running AI analysis pipeline</p>
              <div className="upload-progress">
                <div className="upload-progress-bar" />
              </div>
            </div>
          ) : (
            <>
              <div className="upload-icon-wrapper">
                <div className="upload-icon-bg" />
                <FiUploadCloud className="upload-icon" />
              </div>
              <h2 className="upload-title">Drop your CSV here</h2>
              <p className="upload-sub">
                or <span className="highlight">browse files</span> to launch your analysis
              </p>
              <div className="upload-hint-chip">
                .csv · Max 10MB · Instant AI Processing
              </div>
            </>
          )}

          <input
            type="file"
            accept=".csv"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                onUpload(e.target.files[0]);
              }
            }}
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="hero-stats">
        <div className="hero-stat">
          <div className="stat-num">10x</div>
          <div className="stat-label">Faster Insights</div>
        </div>
        <div className="hero-stat-divider" />
        <div className="hero-stat">
          <div className="stat-num">AI</div>
          <div className="stat-label">Powered Analysis</div>
        </div>
        <div className="hero-stat-divider" />
        <div className="hero-stat">
          <div className="stat-num">∞</div>
          <div className="stat-label">Questions Answered</div>
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
