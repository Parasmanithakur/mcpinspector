import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Wrench as ToolIcon, Play, RefreshCw, Terminal, CheckCircle, AlertCircle, Cpu, Link, Command } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function ShimmerTool() {
  return (
    <div className="tool-item shimmer">
      <div style={{ height: '1.2rem', width: '60%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', marginBottom: '0.4rem' }}></div>
      <div style={{ height: '2.5rem', width: '90%', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}></div>
    </div>
  );
}

function App() {
  const [sessionId] = useState(() => {
    const id = crypto.randomUUID();
    axios.defaults.headers.common['X-Session-ID'] = id;
    console.log("Initialize Browser Session ID:", id);
    return id;
  });
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [args, setArgs] = useState({});
  const [result, setResult] = useState(null);
  const [mcpUrl, setMcpUrl] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');

  const fetchTools = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/tools`);
      setTools(response.data.tools);
      setError(null);
      setConnectionStatus('Connected');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch tools. Is the backend running?');
      setConnectionStatus('Error');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    if (!mcpUrl) return;
    setLoading(true);
    setError(null);
    try {
      await axios.post(`${API_BASE}/connect`, { url: mcpUrl });
      setConnectionStatus('Connected');
      fetchTools();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect to MCP server');
      setConnectionStatus('Error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // No automatic fetch on mount per user request
    console.log("App mounted. Use 'Connect' to onboard an MCP server.");
  }, []);

  const handleToolSelect = (tool) => {
    setSelectedTool(tool);
    setResult(null);
    setArgs({});
  };

  const handleArgChange = (name, value) => {
    setArgs(prev => ({ ...prev, [name]: value }));
  };

  const runTool = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE}/call`, {
        name: selectedTool.name,
        arguments: args
      });
      setResult(response.data.result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute tool');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <Cpu size={28} />
          <span>MCP INSPECTOR</span>
        </div>
        
        <div className="tool-list">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.1em' }}>ONBOARDED TOOLS</span>
            <RefreshCw 
              size={14} 
              className={loading ? 'animate-spin' : ''} 
              style={{ cursor: 'pointer', color: 'var(--accent-color)' }} 
              onClick={fetchTools} 
            />
          </div>
          
          {loading && tools.length === 0 ? (
            <>
              <ShimmerTool />
              <ShimmerTool />
              <ShimmerTool />
            </>
          ) : (
            tools.map(tool => (
              <div 
                key={tool.name} 
                className={`tool-item ${selectedTool?.name === tool.name ? 'active' : ''}`}
                onClick={() => handleToolSelect(tool)}
              >
                <div className="tool-name">{tool.name}</div>
                <div className="tool-desc">{tool.description}</div>
              </div>
            ))
          )}
          
          {tools.length === 0 && !loading && (
            <div className="empty-state" style={{ height: 'auto', marginTop: '2rem' }}>
              No tools available.
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Connection Panel */}
        <section className="glass-panel" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Link size={14} /> MCP URL (SSE)
              </label>
              <input 
                type="text" 
                placeholder="http://localhost:8001/sse" 
                value={mcpUrl}
                onChange={(e) => setMcpUrl(e.target.value)}
              />
            </div>
            <div style={{ width: '200px' }}>
               <label>&nbsp;</label>
               <button 
                className="btn-primary" 
                onClick={handleConnect}
                disabled={loading || !mcpUrl}
                style={{ width: '100%' }}
              >
                {loading ? 'CONNECTING...' : 'CONNECT'}
              </button>
            </div>
          </div>
          <div style={{ marginTop: '1rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ 
              width: 10, height: 10, borderRadius: '50%', 
              boxShadow: connectionStatus === 'Connected' ? '0 0 10px #4ade80' : 'none',
              background: connectionStatus === 'Connected' ? '#10b981' : connectionStatus === 'Error' ? '#ef4444' : '#475569' 
            }} />
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>STATUS: {connectionStatus.toUpperCase()}</span>
          </div>
        </section>

        {selectedTool ? (
          <div className="glass-panel">
            <header style={{ marginBottom: '2.5rem' }}>
              <div className="status-badge status-success" style={{ marginBottom: '1rem' }}>
                <Command size={14} /> READY TO EXECUTE
              </div>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ToolIcon size={32} style={{ color: 'var(--accent-color)' }} /> {selectedTool.name}
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '800px' }}>{selectedTool.description}</p>
            </header>

            <section className="form-section">
              <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>PARAMETERS</h3>
              <div style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {Object.entries(selectedTool.inputSchema.properties || {}).map(([name, schema]) => (
                  <div key={name} className="form-group">
                    <label>
                      {name} {selectedTool.inputSchema.required?.includes(name) && <span style={{ color: 'var(--error-color)' }}>*</span>}
                    </label>
                    <input 
                      type={schema.type === 'number' ? 'number' : 'text'} 
                      placeholder={schema.description || `Enter ${name}`}
                      value={args[name] || ''}
                      onChange={(e) => handleArgChange(name, schema.type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                    />
                  </div>
                ))}
              </div>

              <button 
                className="btn-primary" 
                onClick={runTool}
                disabled={loading}
                style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1rem' }}
              >
                <Play size={18} /> {loading ? 'RUNNING...' : 'EXECUTE TOOL'}
              </button>
            </section>

            {error && (
              <div className="status-badge status-error" style={{ marginTop: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem', width: '100%' }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            {result && (
              <section className="result-panel">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <Terminal size={20} style={{ color: 'var(--accent-color)' }} />
                  <span style={{ fontWeight: 800, fontSize: '0.9rem', letterSpacing: '0.05em' }}>EXECUTION OUTPUT</span>
                </div>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </section>
            )}
          </div>
        ) : (
          <div className="glass-panel" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="empty-state">
              <Box size={80} style={{ opacity: 0.1, marginBottom: '2rem', color: 'var(--accent-color)' }} />
              <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Select a Tool</h3>
              <p>Explore the capabilities of your MCP server by selecting a tool from the left.</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
