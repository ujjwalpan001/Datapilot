import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import FileUpload from './components/FileUpload';
import ColumnsPanel from './components/ColumnsPanel';
import './App.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

// ── Three.js Starfield Background ──────────────────────
function ThreeBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animId;
    let stars = [];
    let width, height;
    let mouseX = 0, mouseY = 0;

    const resize = () => {
      width  = canvas.width  = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const initStars = (count = 280) => {
      stars = Array.from({ length: count }, () => ({
        x:    Math.random() * width,
        y:    Math.random() * height,
        z:    Math.random(),
        size: Math.random() * 1.6 + 0.2,
        vx:   (Math.random() - 0.5) * 0.12,
        vy:   (Math.random() - 0.5) * 0.12,
        hue:  Math.random() > 0.7 ? 200 + Math.random() * 60 : 260 + Math.random() * 40,
        twinkle: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.015 + Math.random() * 0.02,
      }));
    };

    resize();
    initStars();

    window.addEventListener('resize', () => { resize(); initStars(); });
    window.addEventListener('mousemove', (e) => { mouseX = e.clientX; mouseY = e.clientY; });

    // Shooting star
    let shootingStars = [];
    const spawnShooting = () => {
      shootingStars.push({
        x: Math.random() * width * 0.7,
        y: Math.random() * height * 0.5,
        len: 80 + Math.random() * 120,
        speed: 8 + Math.random() * 12,
        angle: Math.PI / 5 + (Math.random() - 0.5) * 0.3,
        life: 1,
        decay: 0.018 + Math.random() * 0.015,
      });
    };
    const shootInterval = setInterval(spawnShooting, 3500);

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Slight mouse parallax offset
      const px = (mouseX / width  - 0.5) * 15;
      const py = (mouseY / height - 0.5) * 15;

      stars.forEach(s => {
        s.twinkle += s.twinkleSpeed;
        const twinkleA = 0.5 + Math.sin(s.twinkle) * 0.5;
        const alpha = (0.3 + s.z * 0.7) * twinkleA;
        const sx = s.x + px * s.z;
        const sy = s.y + py * s.z;

        // Glow for brighter stars
        if (s.z > 0.6) {
          const grd = ctx.createRadialGradient(sx, sy, 0, sx, sy, s.size * 3);
          grd.addColorStop(0, `hsla(${s.hue}, 80%, 80%, ${alpha * 0.6})`);
          grd.addColorStop(1, 'transparent');
          ctx.fillStyle = grd;
          ctx.beginPath();
          ctx.arc(sx, sy, s.size * 3, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.fillStyle = `hsla(${s.hue}, 70%, 90%, ${alpha})`;
        ctx.beginPath();
        ctx.arc(sx, sy, s.size, 0, Math.PI * 2);
        ctx.fill();

        s.x += s.vx;
        s.y += s.vy;
        if (s.x < 0) s.x = width;
        if (s.x > width) s.x = 0;
        if (s.y < 0) s.y = height;
        if (s.y > height) s.y = 0;
      });

      // Shooting stars
      shootingStars = shootingStars.filter(ss => ss.life > 0);
      shootingStars.forEach(ss => {
        const ex = ss.x + Math.cos(ss.angle) * ss.len;
        const ey = ss.y + Math.sin(ss.angle) * ss.len;
        const grd = ctx.createLinearGradient(ss.x, ss.y, ex, ey);
        grd.addColorStop(0, `rgba(255,255,255,0)`);
        grd.addColorStop(0.5, `rgba(200,180,255,${ss.life * 0.8})`);
        grd.addColorStop(1, `rgba(255,255,255,0)`);
        ctx.strokeStyle = grd;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(ss.x, ss.y);
        ctx.lineTo(ex, ey);
        ctx.stroke();
        ss.x += Math.cos(ss.angle) * ss.speed;
        ss.y += Math.sin(ss.angle) * ss.speed;
        ss.life -= ss.decay;
      });

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      clearInterval(shootInterval);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        display: 'block',
      }}
    />
  );
}

// ── Main App Component ──────────────────────────────────
function App() {
  const [session,      setSession]      = useState(null);
  const [messages,     setMessages]     = useState([]);
  const [activeFile,   setActiveFile]   = useState(null);
  const [columns,      setColumns]      = useState([]);
  const [sessionsList, setSessionsList] = useState([]);
  const [isUploading,  setIsUploading]  = useState(false);
  const [query,        setQuery]        = useState('');

  useEffect(() => { fetchSessions(); }, []);

  const fetchSessions = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/sessions`);
      setSessionsList(res.data.sessions);
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/sessions/${sessionId}`);
      setSession(res.data.session);
      setMessages(res.data.messages || []);
      if (res.data.session.filename) {
        setActiveFile(res.data.session.filename);
        fetchColumns(res.data.session.filename);
      }
    } catch (err) {
      console.error('Failed to load session', err);
    }
  };

  const createNewSession = async (filename = null) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/sessions?title=Analysis&filename=${filename || ''}`);
      setSession(res.data);
      setMessages([]);
      fetchSessions();
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  const fetchColumns = async (filename) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/columns/${filename}`);
      setColumns(res.data.columns.map(c => c.name));
    } catch (err) {
      console.error('Failed to fetch columns', err);
    }
  };

  const handleFileUpload = async (file) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_BASE_URL}/upload`, formData);
      const filename = res.data.filename;
      setActiveFile(filename);
      setColumns(res.data.columns);
      if (session) {
        await axios.post(`${API_BASE_URL}/sessions?title=Analysis for ${filename}&filename=${filename}`);
        fetchSessions();
      } else {
        await createNewSession(filename);
      }
      setMessages(prev => [...prev, { role: 'system', content: res.data.message }]);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClearFile = () => {
    setActiveFile(null);
    setColumns([]);
    setMessages([]);
    setSession(null);
  };

  return (
    <div className="app-root">
      {/* Animated canvas starfield */}
      <ThreeBackground />

      {/* Nebula atmospheric blobs */}
      <div className="nebula-overlay" aria-hidden="true">
        <div className="nebula-blob nebula-blob-1" />
        <div className="nebula-blob nebula-blob-2" />
        <div className="nebula-blob nebula-blob-3" />
      </div>

      {/* Grid lines */}
      <div className="grid-overlay" aria-hidden="true" />

      {/* App Shell */}
      <div className="app-container">
        {activeFile && (
          <Sidebar
            sessionsList={sessionsList}
            currentSessionId={session?.id}
            onSelectSession={loadSession}
            onNewSession={() => { setActiveFile(null); setColumns([]); setMessages([]); createNewSession(); }}
            columns={columns}
            activeFile={activeFile}
          />
        )}

        <main className={`main-content ${!activeFile ? 'no-sidebar' : ''}`}>
          {activeFile && (
            <header className="app-header animate-fade-up">
              <div className="header-left">
                <div className="header-logo-icon">✦</div>
                <div className="header-title">
                  <span className="brand">DataPilot</span>
                  <span className="badge">PRO</span>
                </div>
              </div>
              <div className="header-right">
                <div className="file-chip">
                  <span className="file-dot" />
                  <span className="file-name">{activeFile}</span>
                  <button className="close-btn" onClick={handleClearFile}>×</button>
                </div>
                <div className="status-dot">Live</div>
              </div>
            </header>
          )}

          <div className="workspace">
            {activeFile ? (
              <>
                <ChatArea
                  session={session}
                  messages={messages}
                  setMessages={setMessages}
                  activeFile={activeFile}
                  apiBaseUrl={API_BASE_URL}
                  query={query}
                  setQuery={setQuery}
                />
                <ColumnsPanel
                  columns={columns}
                  onColumnClick={(col) => setQuery(`Summarize and show the distribution of "${col}"`)}
                />
              </>
            ) : (
              <FileUpload onUpload={handleFileUpload} isUploading={isUploading} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
