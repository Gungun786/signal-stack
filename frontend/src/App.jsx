import React, { useState, useEffect } from 'react';
import {
  Layers, Compass, Newspaper, CheckCircle2, AlertTriangle, FileText,
  Upload, Settings as SettingsIcon, RefreshCw, Plus, Check, ChevronRight,
  ExternalLink, ShieldCheck, HelpCircle, Activity, ArrowUpRight, Clock,
  Calendar, Building2, Download, AlertCircle, Sparkles, Filter, ChevronDown,
  Link, Wifi, WifiOff
} from 'lucide-react';

const getInitialApiBase = () => {
  const saved = localStorage.getItem('signal_stack_backend_url');
  if (saved) return saved.replace(/\/+$/, '');
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL.replace(/\/+$/, '');
  return '/api';
};

export default function App() {
  const [apiBase, setApiBase] = useState(getInitialApiBase);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'connected' | 'disconnected' | 'checking'
  const [showBackendModal, setShowBackendModal] = useState(false);
  const [backendInput, setBackendInput] = useState(apiBase);
  const [backendTestMsg, setBackendTestMsg] = useState('');

  const [companies, setCompanies] = useState([]);
  const [activeCompany, setActiveCompany] = useState(null);
  const [currentTab, setCurrentTab] = useState('feed');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  // Feed State
  const [signals, setSignals] = useState([]);
  const [feedFilter, setFeedFilter] = useState({ category: '', signal_type: '', urgency: '', verified: false });
  const [selectedSignal, setSelectedSignal] = useState(null);

  // Brief State
  const [briefs, setBriefs] = useState([]);
  const [currentBrief, setCurrentBrief] = useState(null);

  // Sources State
  const [sources, setSources] = useState([]);
  const [sourceCategory, setSourceCategory] = useState('all');
  const [showAddSourceModal, setShowAddSourceModal] = useState(false);
  const [newSourceForm, setNewSourceForm] = useState({ name: '', url: '', category: 'competitors', reason: '' });

  // Profile State
  const [profile, setProfile] = useState(null);

  // Interview State
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [interviewAnswer, setInterviewAnswer] = useState('');

  // Pivot / Context Change State
  const [pivotContext, setPivotContext] = useState('');
  const [pivotLogs, setPivotLogs] = useState([]);

  // Scheduler Logs
  const [schedulerLogs, setSchedulerLogs] = useState([]);

  // New Company Modal
  const [showNewCompanyModal, setShowNewCompanyModal] = useState(false);
  const [newCompanyForm, setNewCompanyForm] = useState({ name: '', website: '', context: '' });

  // Fetch Companies on Load & whenever apiBase changes
  useEffect(() => {
    fetchCompanies(apiBase);
    fetchSchedulerLogs(apiBase);
  }, [apiBase]);

  // When Active Company Changes, reload data
  useEffect(() => {
    if (activeCompany) {
      loadCompanyData(activeCompany.id, apiBase);
    }
  }, [activeCompany, apiBase]);

  const fetchCompanies = async (baseUrl = apiBase) => {
    setBackendStatus('checking');
    try {
      const res = await fetch(`${baseUrl}/companies`);
      if (!res.ok) {
        setBackendStatus('disconnected');
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setCompanies(data);
        setBackendStatus('connected');
        if (data.length > 0 && !activeCompany) {
          setActiveCompany(data[0]);
        }
      } else {
        setBackendStatus('disconnected');
      }
    } catch (err) {
      console.error('Error fetching companies:', err);
      setBackendStatus('disconnected');
    }
  };

  const loadCompanyData = async (compId, baseUrl = apiBase) => {
    setLoading(true);
    try {
      // 1. Signals Feed
      const sigRes = await fetch(`${baseUrl}/companies/${compId}/signals`);
      if (sigRes.ok) {
        const sigData = await sigRes.json();
        setSignals(sigData);
      }

      // 2. Sources
      const srcRes = await fetch(`${baseUrl}/companies/${compId}/sources`);
      if (srcRes.ok) {
        const srcData = await srcRes.json();
        setSources(srcData);
      }

      // 3. Profile
      const profRes = await fetch(`${baseUrl}/companies/${compId}/profile`);
      if (profRes.ok) {
        const profData = await profRes.json();
        setProfile(profData);
      }

      // 4. Briefs
      const briefRes = await fetch(`${baseUrl}/companies/${compId}/briefs`);
      if (briefRes.ok) {
        const briefData = await briefRes.json();
        setBriefs(briefData);
        if (briefData.length > 0) setCurrentBrief(briefData[0]);
      }

      // 5. Interview Questions
      const intRes = await fetch(`${baseUrl}/companies/${compId}/interview/all`);
      if (intRes.ok) {
        const intData = await intRes.json();
        setInterviewQuestions(intData);
      }

      // 6. Current Interview Step
      const currRes = await fetch(`${baseUrl}/companies/${compId}/interview/current`);
      if (currRes.ok) {
        const currData = await currRes.json();
        setCurrentQuestion(currData);
      }

      // 7. Pivot Logs
      const pivRes = await fetch(`${baseUrl}/companies/${compId}/context-changes`);
      if (pivRes.ok) {
        const pivData = await pivRes.json();
        setPivotLogs(pivData);
      }
    } catch (e) {
      console.error('Error loading company data:', e);
    }
    setLoading(false);
  };

  const fetchSchedulerLogs = async (baseUrl = apiBase) => {
    try {
      const res = await fetch(`${baseUrl}/scheduler/logs`);
      if (res.ok) {
        const data = await res.json();
        setSchedulerLogs(data);
      }
    } catch (e) {
      console.error('Error fetching logs:', e);
    }
  };

  const handleTestAndSaveBackend = async () => {
    let input = backendInput.trim().replace(/\/+$/, '');
    if (!input) input = '/api';
    if (!input.startsWith('http') && !input.startsWith('/')) {
      input = `https://${input}`;
    }

    setBackendTestMsg('Testing connection...');
    try {
      // Test URL both with and without /api
      let targetUrl = input;
      let res = await fetch(`${targetUrl}/companies`).catch(() => null);
      if (!res || !res.ok) {
        if (!targetUrl.endsWith('/api')) {
          targetUrl = `${targetUrl}/api`;
          res = await fetch(`${targetUrl}/companies`).catch(() => null);
        }
      }

      if (res && res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          localStorage.setItem('signal_stack_backend_url', targetUrl);
          setApiBase(targetUrl);
          setBackendStatus('connected');
          setBackendTestMsg(`Connected successfully! Found ${data.length} companies.`);
          setTimeout(() => {
            setShowBackendModal(false);
            setBackendTestMsg('');
          }, 1200);
          fetchCompanies(targetUrl);
          return;
        }
      }
      setBackendTestMsg('Failed: Backend returned non-JSON or error. Make sure your Render web service is live.');
    } catch (err) {
      setBackendTestMsg(`Connection error: ${err.message}. If using Render free tier, allow up to 45s for cold start.`);
    }
  };

  const handleRunMonitor = async () => {
    if (!activeCompany) return;
    setLoading(true);
    setStatusMsg('Crawling approved sources & synthesizing signals...');
    try {
      const res = await fetch(`${apiBase}/companies/${activeCompany.id}/monitor`, { method: 'POST' });
      const data = await res.json();
      setStatusMsg(`Monitoring complete: ${data.new_items_crawled} new items, ${data.signals_generated} signals analyzed.`);
      loadCompanyData(activeCompany.id);
    } catch (e) {
      setStatusMsg('Error running monitor cycle.');
    }
    setLoading(false);
    setTimeout(() => setStatusMsg(''), 5000);
  };

  const handleGenerateBrief = async () => {
    if (!activeCompany) return;
    setLoading(true);
    setStatusMsg('Compiling Monday Morning Intelligence Brief...');
    try {
      const res = await fetch(`${apiBase}/companies/${activeCompany.id}/briefs/generate`, { method: 'POST' });
      const data = await res.json();
      setCurrentBrief(data);
      setStatusMsg('New Monday Brief compiled successfully!');
      loadCompanyData(activeCompany.id);
    } catch (e) {
      setStatusMsg('Error generating brief.');
    }
    setLoading(false);
    setTimeout(() => setStatusMsg(''), 5000);
  };

  const handleAnswerInterview = async (skip = false) => {
    if (!activeCompany || !currentQuestion) return;
    try {
      await fetch(`${apiBase}/companies/${activeCompany.id}/interview/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step_number: currentQuestion.step_number,
          answer_text: skip ? null : interviewAnswer,
          skipped: skip
        })
      });
      setInterviewAnswer('');
      const currRes = await fetch(`${apiBase}/companies/${activeCompany.id}/interview/current`);
      const currData = await currRes.json();
      setCurrentQuestion(currData);
      loadCompanyData(activeCompany.id);
    } catch (e) {
      console.error('Error submitting answer:', e);
    }
  };

  const handleToggleAction = async (briefId, index, currentStatus) => {
    const nextStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    try {
      await fetch(`${apiBase}/briefs/${briefId}/actions`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action_index: index, status: nextStatus })
      });
      const updatedActions = [...currentBrief.recommended_actions];
      updatedActions[index].status = nextStatus;
      setCurrentBrief({ ...currentBrief, recommended_actions: updatedActions });
    } catch (e) {
      console.error('Error toggling action:', e);
    }
  };

  const handleApplyPivot = async () => {
    if (!activeCompany || !pivotContext.trim()) return;
    setLoading(true);
    setStatusMsg('Re-assessing sources against updated strategic focus...');
    try {
      const res = await fetch(`${apiBase}/companies/${activeCompany.id}/context-change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_context: pivotContext })
      });
      const data = await res.json();
      setStatusMsg(`Pivot applied! Added ${data.sources_added.length} sources, deprecated ${data.sources_deprecated.length}.`);
      setPivotContext('');
      loadCompanyData(activeCompany.id);
    } catch (e) {
      setStatusMsg('Error applying strategic pivot.');
    }
    setLoading(false);
    setTimeout(() => setStatusMsg(''), 5000);
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    if (!newCompanyForm.name || !newCompanyForm.website) return;
    setLoading(true);
    setStatusMsg('Creating company and conducting initial research crawl...');
    try {
      const res = await fetch(`${apiBase}/companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCompanyForm)
      });
      const comp = await res.json();
      setShowNewCompanyModal(false);
      setNewCompanyForm({ name: '', website: '', context: '' });
      await fetchCompanies();
      setActiveCompany(comp);
      setStatusMsg(`Company '${comp.name}' initialized.`);
    } catch (err) {
      setStatusMsg('Failed to initialize company.');
    }
    setLoading(false);
    setTimeout(() => setStatusMsg(''), 5000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !activeCompany) return;
    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    setStatusMsg(`Ingesting ${file.name}...`);
    try {
      const res = await fetch(`${apiBase}/companies/${activeCompany.id}/internal/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setStatusMsg(`Successfully extracted ${data.extracted_signals} internal signals from ${file.name}!`);
      loadCompanyData(activeCompany.id);
    } catch (err) {
      setStatusMsg('Error uploading internal document.');
    }
    setLoading(false);
    setTimeout(() => setStatusMsg(''), 5000);
  };

  const filteredSignals = signals.filter(s => {
    if (feedFilter.category && s.category !== feedFilter.category) return false;
    if (feedFilter.signal_type && s.signal_type !== feedFilter.signal_type) return false;
    if (feedFilter.urgency && s.urgency !== feedFilter.urgency) return false;
    if (feedFilter.verified && !s.verified) return false;
    return true;
  });

  const filteredSources = sources.filter(s => {
    if (sourceCategory === 'all') return true;
    return s.category === sourceCategory;
  });

  return (
    <div className="app-container">
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
          <div style={{ background: '#2563eb', padding: 8, borderRadius: 8, display: 'flex' }}>
            <Layers size={20} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 800, letterSpacing: '-0.02em' }}>SIGNAL STACK</h2>
            <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>Intelligence Engine</p>
          </div>
        </div>

        {/* Company Selector */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 8 }}>
            Active Entity
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <select
              className="input-field"
              style={{ fontSize: 13, padding: '8px 10px', background: 'var(--bg-tertiary)' }}
              value={activeCompany ? activeCompany.id : ''}
              onChange={(e) => {
                const selected = companies.find(c => c.id === parseInt(e.target.value));
                if (selected) setActiveCompany(selected);
              }}
            >
              {companies.length === 0 && <option value="">No companies loaded</option>}
              {companies.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button
              className="btn btn-secondary"
              style={{ padding: '8px 10px' }}
              title="Add Company"
              onClick={() => setShowNewCompanyModal(true)}
            >
              <Plus size={16} />
            </button>
          </div>
          {activeCompany && (
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
              <ExternalLink size={10} /> {activeCompany.website}
            </p>
          )}
        </div>

        {/* Nav Tabs */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
          {[
            { id: 'feed', label: 'Intelligence Feed', icon: Newspaper, count: signals.length },
            { id: 'brief', label: 'Monday Brief', icon: FileText, count: briefs.length },
            { id: 'sources', label: 'Signal Stack', icon: Compass, count: sources.length },
            { id: 'profile', label: 'Company Profile', icon: Building2 },
            { id: 'interview', label: 'Adaptive Interview', icon: Sparkles, count: `${interviewQuestions.filter(q => q.answer_text).length}/10` },
            { id: 'upload', label: 'Internal Upload', icon: Upload },
            { id: 'pivot', label: 'Context Pivot', icon: RefreshCw },
            { id: 'logs', label: 'Scheduler Logs', icon: Clock, count: schedulerLogs.length },
            { id: 'settings', label: 'Settings', icon: SettingsIcon }
          ].map(item => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: 'none',
                  background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  color: isActive ? '#60a5fa' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: 13,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <Icon size={16} />
                  <span>{item.label}</span>
                </div>
                {item.count !== undefined && (
                  <span style={{ fontSize: 11, padding: '1px 6px', borderRadius: 10, background: isActive ? '#2563eb' : 'var(--bg-tertiary)', color: 'white' }}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Backend Connectivity Status Widget */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)' }}>BACKEND API</span>
            <span
              className={`badge ${backendStatus === 'connected' ? 'badge-emerald' : (backendStatus === 'checking' ? 'badge-amber' : 'badge-rose')}`}
              style={{ cursor: 'pointer' }}
              onClick={() => setShowBackendModal(true)}
              title="Click to configure backend URL"
            >
              {backendStatus === 'connected' ? 'Connected' : (backendStatus === 'checking' ? 'Connecting...' : 'Set URL')}
            </span>
          </div>
          <button
            onClick={() => setShowBackendModal(true)}
            style={{
              width: '100%',
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border)',
              color: 'var(--text-secondary)',
              padding: '6px 10px',
              borderRadius: 6,
              fontSize: 11,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }}>
              {apiBase}
            </span>
            <Link size={12} />
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">
        {/* Disconnected Backend Warning Banner */}
        {backendStatus === 'disconnected' && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            color: '#fca5a5',
            padding: '14px 18px',
            borderRadius: 10,
            marginBottom: 24,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 16
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <AlertTriangle size={20} color="#ef4444" style={{ flexShrink: 0 }} />
              <div>
                <strong style={{ fontSize: 14, color: '#f87171' }}>Backend Connection Required</strong>
                <p style={{ fontSize: 12, marginTop: 2, color: '#fecaca' }}>
                  The frontend cannot reach the backend API at <code>{apiBase}</code>.
                  If you deployed your backend on Render, paste your live Render URL to connect immediately.
                </p>
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => setShowBackendModal(true)}
              style={{ background: '#ef4444', flexShrink: 0, fontSize: 12 }}
            >
              Set Backend URL
            </button>
          </div>
        )}

        {/* Top Header Bar */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              {currentTab === 'feed' && 'Ranked Intelligence Feed'}
              {currentTab === 'brief' && 'Monday Morning Executive Brief'}
              {currentTab === 'sources' && 'Signal Stack Sources & Health'}
              {currentTab === 'profile' && 'Intelligence Profile (Empirical vs Inferred)'}
              {currentTab === 'interview' && 'Adaptive AI Executive Interview'}
              {currentTab === 'upload' && 'Internal Data & Objection Ingestion'}
              {currentTab === 'pivot' && 'Strategic Context Pivot & Alignment'}
              {currentTab === 'logs' && 'Scheduler & Cron Execution History'}
              {currentTab === 'settings' && 'Configuration & Controls'}
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              Tracking company signals for <strong>{activeCompany ? activeCompany.name : 'All Entities'}</strong>
            </p>
          </div>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            {statusMsg && (
              <span style={{ fontSize: 12, color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '6px 12px', borderRadius: 6 }}>
                {statusMsg}
              </span>
            )}
            <button
              className="btn btn-secondary"
              onClick={handleRunMonitor}
              disabled={loading || !activeCompany}
              title="Run Crawler Cycle"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>Crawl & Refresh</span>
            </button>
            <button
              className="btn btn-primary"
              onClick={handleGenerateBrief}
              disabled={loading || !activeCompany}
              title="Generate Fresh Brief"
            >
              <Sparkles size={14} />
              <span>Compile Brief</span>
            </button>
          </div>
        </header>

        {/* TAB 1: INTELLIGENCE FEED */}
        {currentTab === 'feed' && (
          <div>
            {/* Filter Bar */}
            <div className="glass-card" style={{ marginBottom: 20, padding: 16, display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: 13 }}>
                <Filter size={14} /> Filters:
              </div>
              <select
                className="input-field"
                style={{ width: 'auto', padding: '6px 12px', fontSize: 13 }}
                value={feedFilter.category}
                onChange={e => setFeedFilter({ ...feedFilter, category: e.target.value })}
              >
                <option value="">All Categories</option>
                <option value="customers">Customers</option>
                <option value="competitors">Competitors</option>
                <option value="market">Market</option>
                <option value="internal">Internal</option>
              </select>

              <select
                className="input-field"
                style={{ width: 'auto', padding: '6px 12px', fontSize: 13 }}
                value={feedFilter.signal_type}
                onChange={e => setFeedFilter({ ...feedFilter, signal_type: e.target.value })}
              >
                <option value="">All Types</option>
                <option value="opportunity">Opportunity</option>
                <option value="threat">Threat</option>
                <option value="neutral">Neutral</option>
              </select>

              <select
                className="input-field"
                style={{ width: 'auto', padding: '6px 12px', fontSize: 13 }}
                value={feedFilter.urgency}
                onChange={e => setFeedFilter({ ...feedFilter, urgency: e.target.value })}
              >
                <option value="">All Urgencies</option>
                <option value="immediate">Immediate</option>
                <option value="this_week">This Week</option>
                <option value="monitor">Monitor</option>
              </select>

              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                <input
                  type="checkbox"
                  checked={feedFilter.verified}
                  onChange={e => setFeedFilter({ ...feedFilter, verified: e.target.checked })}
                />
                Verified Evidence Only
              </label>

              <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-muted)' }}>
                Showing {filteredSignals.length} of {signals.length} signals
              </span>
            </div>

            {/* Signal Feed Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {filteredSignals.length === 0 ? (
                <div className="glass-card" style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                  <HelpCircle size={32} style={{ margin: '0 auto 12px' }} />
                  <p>
                    {backendStatus === 'disconnected'
                      ? 'Backend not connected yet. Click "Set Backend URL" in the sidebar to connect.'
                      : 'No signals found for this entity. Click "Crawl & Refresh" to harvest sources.'}
                  </p>
                </div>
              ) : (
                filteredSignals.map(sig => (
                  <div
                    key={sig.id}
                    className="glass-card"
                    style={{ padding: 20, cursor: 'pointer' }}
                    onClick={() => setSelectedSignal(sig)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                        <span className={`badge ${
                          sig.category === 'competitors' ? 'badge-rose' :
                          sig.category === 'customers' ? 'badge-emerald' :
                          sig.category === 'market' ? 'badge-blue' : 'badge-amber'
                        }`}>
                          {sig.category}
                        </span>

                        <span className={`badge ${
                          sig.signal_type === 'opportunity' ? 'badge-emerald' :
                          sig.signal_type === 'threat' ? 'badge-rose' : 'badge-indigo'
                        }`}>
                          {sig.signal_type}
                        </span>

                        {sig.verified ? (
                          <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                            <ShieldCheck size={10} /> Verified Fact
                          </span>
                        ) : (
                          <span className="badge badge-amber">Unverified</span>
                        )}

                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                          Area: <strong style={{ color: 'var(--text-secondary)' }}>{sig.affected_business_area}</strong>
                        </span>
                      </div>

                      {/* Rank Score Pill */}
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: '#38bdf8' }}>
                          {sig.rank_score}/100
                        </div>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rank Score</span>
                      </div>
                    </div>

                    <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, lineHeight: 1.4, color: 'var(--text-primary)' }}>
                      {sig.what_happened}
                    </h3>

                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
                      <strong style={{ color: '#93c5fd' }}>Why it matters: </strong>
                      {sig.why_it_matters}
                    </p>

                    {/* Evidence Snippet Quote */}
                    <div style={{ background: 'rgba(15, 23, 42, 0.6)', borderLeft: '3px solid #3b82f6', padding: '8px 12px', borderRadius: '0 6px 6px 0', marginBottom: 12 }}>
                      <p style={{ fontSize: 12, color: '#cbd5e1', fontStyle: 'italic' }}>
                        "{sig.evidence_snippet}"
                      </p>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--text-muted)' }}>
                      <div style={{ display: 'flex', gap: 16 }}>
                        <span>Relevance: <strong>{sig.strategic_relevance}%</strong></span>
                        <span>Impact: <strong>{sig.business_impact}%</strong></span>
                        <span>Credibility: <strong>{sig.source_credibility}%</strong></span>
                      </div>
                      <a
                        href={sig.source_url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={e => e.stopPropagation()}
                        style={{ color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}
                      >
                        Source Link <ArrowUpRight size={12} />
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Signal Detail Modal */}
            {selectedSignal && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20 }}>
                <div className="glass-card" style={{ maxWidth: 700, width: '100%', maxHeight: '90vh', overflowY: 'auto', background: 'var(--bg-secondary)', border: '1px solid rgba(148, 163, 184, 0.3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <span className="badge badge-blue">{selectedSignal.category.toUpperCase()} SIGNAL</span>
                    <button onClick={() => setSelectedSignal(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}>✕</button>
                  </div>

                  <h2 style={{ fontSize: 18, fontWeight: 800, marginBottom: 12 }}>{selectedSignal.what_happened}</h2>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16, background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8 }}>
                    <div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>VERIFICATION STATUS</span>
                      <p style={{ fontSize: 13, fontWeight: 600, color: selectedSignal.verified ? '#34d399' : '#fbbf24' }}>
                        {selectedSignal.verified ? 'Verified Empirical Fact' : 'Unverified / Speculation'}
                      </p>
                      <small style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{selectedSignal.verification_reasoning}</small>
                    </div>
                    <div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>RANK EXPLANATION</span>
                      <p style={{ fontSize: 12, color: 'var(--text-primary)' }}>{selectedSignal.rank_explanation}</p>
                    </div>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <h4 style={{ fontSize: 12, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 4 }}>Why It Matters</h4>
                    <p style={{ fontSize: 13, lineHeight: 1.5 }}>{selectedSignal.why_it_matters}</p>
                  </div>

                  <div style={{ marginBottom: 16 }}>
                    <h4 style={{ fontSize: 12, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 4 }}>Suggested Strategic Action</h4>
                    <p style={{ fontSize: 13, lineHeight: 1.5, color: '#93c5fd' }}>{selectedSignal.suggested_action}</p>
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <h4 style={{ fontSize: 12, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 4 }}>Full Evidence Snippet</h4>
                    <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6, fontSize: 12, fontStyle: 'italic', color: '#cbd5e1' }}>
                      "{selectedSignal.evidence_snippet}"
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: 14 }}>
                    <a href={selectedSignal.source_url} target="_blank" rel="noreferrer" className="btn btn-primary">
                      Open Verified Source <ExternalLink size={14} />
                    </a>
                    <button onClick={() => setSelectedSignal(null)} className="btn btn-secondary">Close</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MONDAY MORNING BRIEF */}
        {currentTab === 'brief' && (
          <div>
            {currentBrief ? (
              <div>
                <div className="glass-card" style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span className="badge badge-blue" style={{ marginBottom: 6 }}>WEEKLY EXECUTIVE BRIEF</span>
                    <h2 style={{ fontSize: 20, fontWeight: 800 }}>{currentBrief.title}</h2>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      Generated on {new Date(currentBrief.created_at).toUTCString()} &bull; Period: Last 7 Days
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 10 }}>
                    <a
                      href={`${apiBase}/briefs/${currentBrief.id}/export/markdown`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                    >
                      <Download size={14} /> Export Markdown
                    </a>
                    <a
                      href={`${apiBase}/briefs/${currentBrief.id}/export/html`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary"
                    >
                      <Download size={14} /> Export HTML
                    </a>
                  </div>
                </div>

                {/* 1. Executive Summary (Top 5) */}
                <div className="glass-card" style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CheckCircle2 size={18} color="#3b82f6" /> 1. Executive Summary (Top 5 Developments)
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {currentBrief.executive_summary.map((item, idx) => (
                      <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <span className="badge badge-blue" style={{ marginRight: 8 }}>{item.category}</span>
                          <span style={{ fontSize: 13, fontWeight: 600 }}>{item.headline}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <span className="badge badge-amber">{item.urgency}</span>
                          <a href={item.source_url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}><ArrowUpRight size={14} /></a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Recommended Actions Checklist */}
                <div className="glass-card" style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CheckCircle2 size={18} color="#10b981" /> 2. Prioritized Recommended Actions (Track Status)
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {currentBrief.recommended_actions.map((act, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: act.status === 'completed' ? 'rgba(16, 185, 129, 0.08)' : 'var(--bg-tertiary)',
                          border: act.status === 'completed' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--border)',
                          padding: 14,
                          borderRadius: 8,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 14
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={act.status === 'completed'}
                          onChange={() => handleToggleAction(currentBrief.id, idx, act.status)}
                          style={{ width: 18, height: 18, cursor: 'pointer' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span className={`badge ${act.priority === 'P0' ? 'badge-rose' : 'badge-amber'}`}>{act.priority}</span>
                            <span style={{ fontSize: 13, fontWeight: 700, textDecoration: act.status === 'completed' ? 'line-through' : 'none' }}>
                              {act.action}
                            </span>
                          </div>
                          <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>{act.reason}</p>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block' }}>Owner:</span>
                          <strong style={{ fontSize: 12, color: '#38bdf8' }}>{act.owner}</strong>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Opportunities & Risks */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
                  <div className="glass-card">
                    <h3 style={{ fontSize: 15, fontWeight: 800, marginBottom: 14, color: '#34d399' }}>
                      Strategic Opportunities (3+)
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {currentBrief.opportunities.map((opp, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <strong style={{ fontSize: 13 }}>{opp.title}</strong>
                            <span className="badge badge-emerald">{opp.priority}</span>
                          </div>
                          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>{opp.evidence}</p>
                          <p style={{ fontSize: 12, color: '#93c5fd' }}><strong>Next Step: </strong>{opp.next_step}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="glass-card">
                    <h3 style={{ fontSize: 15, fontWeight: 800, marginBottom: 14, color: '#fb7185' }}>
                      Material Risks & Threats
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {currentBrief.risks_and_threats.map((r, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <strong style={{ fontSize: 13 }}>{r.threat}</strong>
                            <span className="badge badge-rose">{r.severity} Severity</span>
                          </div>
                          <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>Mitigation: </strong>{r.mitigation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 4. Source Appendix Table */}
                <div className="glass-card">
                  <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16 }}>
                    Evidence & Source Appendix ({currentBrief.source_appendix.length} records)
                  </h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                      <thead>
                        <tr style={{ background: 'var(--bg-tertiary)', textAlign: 'left' }}>
                          <th style={{ padding: 10 }}>Source</th>
                          <th style={{ padding: 10 }}>Pub Date</th>
                          <th style={{ padding: 10 }}>Verification</th>
                          <th style={{ padding: 10 }}>Snippet</th>
                          <th style={{ padding: 10 }}>Link</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentBrief.source_appendix.slice(0, 15).map((app, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                            <td style={{ padding: 10, fontWeight: 600 }}>{app.source}</td>
                            <td style={{ padding: 10, color: 'var(--text-muted)' }}>{app.publication_date}</td>
                            <td style={{ padding: 10 }}><span className="badge badge-emerald">{app.verification_status}</span></td>
                            <td style={{ padding: 10, color: 'var(--text-secondary)', maxWidth: 300 }}>{app.snippet}</td>
                            <td style={{ padding: 10 }}>
                              <a href={app.link} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}><ExternalLink size={12} /></a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ textAlign: 'center', padding: 48 }}>
                <FileText size={32} style={{ margin: '0 auto 12px', color: 'var(--text-muted)' }} />
                <p>No brief compiled yet for this entity. Click 'Compile Brief' to create one from live signals.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SIGNAL STACK / SOURCES */}
        {currentTab === 'sources' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 8 }}>
                {['all', 'competitors', 'customers', 'market', 'internal'].map(cat => (
                  <button
                    key={cat}
                    onClick={() => setSourceCategory(cat)}
                    className={`btn ${sourceCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ textTransform: 'capitalize', fontSize: 12 }}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              <button
                className="btn btn-secondary"
                onClick={() => setShowAddSourceModal(true)}
              >
                <Plus size={14} /> Add Source Channel
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
              {filteredSources.map(s => (
                <div key={s.id} className="glass-card" style={{ padding: 18, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span className={`badge ${
                        s.category === 'competitors' ? 'badge-rose' :
                        s.category === 'customers' ? 'badge-emerald' :
                        s.category === 'market' ? 'badge-blue' : 'badge-amber'
                      }`}>
                        {s.category}
                      </span>
                      <span className={`badge ${s.health_status === 'healthy' ? 'badge-emerald' : 'badge-amber'}`}>
                        {s.health_status}
                      </span>
                    </div>

                    <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>{s.name}</h4>
                    <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.4 }}>
                      {s.reason_for_inclusion}
                    </p>
                  </div>

                  <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
                    <span>Credibility: <strong style={{ color: 'var(--text-primary)' }}>{s.credibility_score}%</strong></span>
                    <a href={s.url} target="_blank" rel="noreferrer" style={{ color: '#60a5fa', display: 'flex', alignItems: 'center', gap: 3 }}>
                      URL <ExternalLink size={10} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: INTELLIGENCE PROFILE */}
        {currentTab === 'profile' && profile && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Products & Platform Offerings</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {profile.products.map((p, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13 }}>{p.item}</span>
                    <span className={`badge ${p.status === 'verified' ? 'badge-emerald' : 'badge-amber'}`}>
                      {p.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Target Customers & Segments</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {profile.customers.map((c, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13 }}>{c.item}</span>
                    <span className={`badge ${c.status === 'verified' ? 'badge-emerald' : 'badge-amber'}`}>
                      {c.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Positioning & Moat Claims</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {profile.positioning.map((pos, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 13 }}>{pos.item}</span>
                    <span className={`badge ${pos.status === 'verified' ? 'badge-emerald' : 'badge-amber'}`}>
                      {pos.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: ADAPTIVE AI INTERVIEW */}
        {currentTab === 'interview' && (
          <div>
            {currentQuestion && currentQuestion.step_number <= 10 && !currentQuestion.answer_text ? (
              <div className="glass-card" style={{ marginBottom: 28, border: '1px solid #3b82f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span className="badge badge-blue">STEP {currentQuestion.step_number} OF 10 &bull; {currentQuestion.domain.toUpperCase()}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Confidential questions can be skipped</span>
                </div>

                <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 8 }}>{currentQuestion.question_text}</h3>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>{currentQuestion.suggested_context}</p>

                <textarea
                  className="input-field"
                  rows={4}
                  placeholder="Provide executive context or specifics..."
                  value={interviewAnswer}
                  onChange={e => setInterviewAnswer(e.target.value)}
                  style={{ marginBottom: 16 }}
                />

                <div style={{ display: 'flex', gap: 12 }}>
                  <button className="btn btn-primary" onClick={() => handleAnswerInterview(false)} disabled={!interviewAnswer.trim()}>
                    Submit Strategic Answer
                  </button>
                  <button className="btn btn-secondary" onClick={() => handleAnswerInterview(true)}>
                    Skip (Confidential)
                  </button>
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ marginBottom: 24, textAlign: 'center', padding: 24 }}>
                <CheckCircle2 size={32} color="#10b981" style={{ margin: '0 auto 8px' }} />
                <h3>All 10 Executive Questions Completed!</h3>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                  Answers have been incorporated into the dynamic source generation and ranking matrix.
                </p>
              </div>
            )}

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16 }}>Interview Record (10 Steps)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {interviewQuestions.map(q => (
                  <div key={q.id} style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span className="badge badge-indigo">Step {q.step_number}: {q.domain}</span>
                      {q.skipped ? <span className="badge badge-amber">Skipped</span> : <span className="badge badge-emerald">Answered</span>}
                    </div>
                    <strong style={{ fontSize: 13, display: 'block', marginBottom: 6 }}>{q.question_text}</strong>
                    <p style={{ fontSize: 12, color: q.answer_text ? '#93c5fd' : 'var(--text-muted)' }}>
                      {q.answer_text ? `Answer: ${q.answer_text}` : 'Skipped for strategic confidentiality.'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: INTERNAL FILE UPLOAD */}
        {currentTab === 'upload' && (
          <div className="glass-card" style={{ textAlign: 'center', padding: 48 }}>
            <Upload size={40} color="#3b82f6" style={{ margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 8 }}>Ingest Internal Documents</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 500, margin: '0 auto 24px' }}>
              Upload CSV, Excel (.xlsx), PDF, or text files containing customer objections, lost-deal CRM notes, or support transcripts.
            </p>

            <label className="btn btn-primary" style={{ cursor: 'pointer', display: 'inline-flex' }}>
              <Upload size={14} /> Select Document
              <input type="file" accept=".csv,.xlsx,.xls,.pdf,.txt,.md" style={{ display: 'none' }} onChange={handleFileUpload} />
            </label>
          </div>
        )}

        {/* TAB 7: CONTEXT PIVOT */}
        {currentTab === 'pivot' && (
          <div>
            <div className="glass-card" style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 8 }}>Strategic Context Change Engine</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                When your company launches a new product line or pivots focus, input the new strategic context.
                The system will automatically re-evaluate existing sources, deprecate outdated competitors, and discover newly aligned channels.
              </p>

              <textarea
                className="input-field"
                rows={3}
                placeholder="e.g. Pivoting from local consumer admissions to B2B enterprise university recruitment and AI enrollment agents..."
                value={pivotContext}
                onChange={e => setPivotContext(e.target.value)}
                style={{ marginBottom: 14 }}
              />

              <button className="btn btn-primary" onClick={handleApplyPivot} disabled={!pivotContext.trim()}>
                Apply Strategic Pivot
              </button>
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16 }}>Pivot Audit Trail</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {pivotLogs.map(log => (
                  <div key={log.id} style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span className="badge badge-blue">PIVOT AUDIT #{log.id}</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{new Date(log.created_at).toUTCString()}</span>
                    </div>
                    <p style={{ fontSize: 13, fontWeight: 600, color: '#38bdf8', marginBottom: 6 }}>{log.explanation}</p>
                    <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
                      <span>Sources Added: <strong>{log.sources_added.length}</strong></span>
                      <span>Sources Deprecated: <strong>{log.sources_deprecated.length}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: SCHEDULER LOGS */}
        {currentTab === 'logs' && (
          <div className="glass-card">
            <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 16 }}>Autonomous Scheduler Run Logs</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: 'var(--bg-tertiary)', textAlign: 'left' }}>
                    <th style={{ padding: 10 }}>Job Type</th>
                    <th style={{ padding: 10 }}>Status</th>
                    <th style={{ padding: 10 }}>Executed At</th>
                    <th style={{ padding: 10 }}>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {schedulerLogs.map(log => (
                    <tr key={log.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: 10, fontWeight: 600 }}>{log.job_type}</td>
                      <td style={{ padding: 10 }}>
                        <span className={`badge ${log.status === 'success' ? 'badge-emerald' : 'badge-rose'}`}>
                          {log.status}
                        </span>
                      </td>
                      <td style={{ padding: 10, color: 'var(--text-muted)' }}>{new Date(log.executed_at).toUTCString()}</td>
                      <td style={{ padding: 10, color: 'var(--text-secondary)' }}>{log.details}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 9: SETTINGS & BACKEND CONFIG */}
        {currentTab === 'settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Backend API Connection</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Active backend endpoint: <code>{apiBase}</code> (Status: <strong style={{ color: backendStatus === 'connected' ? '#34d399' : '#f87171' }}>{backendStatus}</strong>)
              </p>
              <button className="btn btn-primary" onClick={() => setShowBackendModal(true)}>
                <Link size={14} /> Change Backend URL
              </button>
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Automation Cadence</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 8 }}>
                  <strong>Weekly Brief Cron</strong>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Every Monday at 06:00 UTC</p>
                  <span className="badge badge-emerald" style={{ marginTop: 8 }}>Active</span>
                </div>
                <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 8 }}>
                  <strong>Monthly Audit Cron</strong>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>1st of every month at 00:00 UTC</p>
                  <span className="badge badge-emerald" style={{ marginTop: 8 }}>Active</span>
                </div>
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12 }}>Free Tier Guarantee Summary</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                Signal Stack is architected exclusively on 100% free-tier services. All crawling uses open-source scrapers and public RSS endpoints.
                LLMs operate on Google AI Studio Free Tier (15 RPM, 1M TPM) with automatic failover to Groq Cloud Free Tier.
              </p>
            </div>
          </div>
        )}

        {/* MODAL: CONFIGURE BACKEND URL */}
        {showBackendModal && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110, padding: 20 }}>
            <div className="glass-card" style={{ maxWidth: 520, width: '100%', background: 'var(--bg-secondary)' }}>
              <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Link size={18} color="#3b82f6" /> Connect Backend Service
              </h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>
                Enter the URL of your deployed Render service (e.g. <code>https://signal-stack-backend.onrender.com</code>) or your local dev server (<code>http://localhost:8000/api</code>).
              </p>

              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Backend Service URL</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="https://your-service.onrender.com"
                  value={backendInput}
                  onChange={e => setBackendInput(e.target.value)}
                />
              </div>

              {backendTestMsg && (
                <div style={{
                  fontSize: 12,
                  padding: '8px 12px',
                  borderRadius: 6,
                  marginBottom: 14,
                  background: backendTestMsg.includes('Connected') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: backendTestMsg.includes('Connected') ? '#34d399' : '#fca5a5'
                }}>
                  {backendTestMsg}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button type="button" className="btn btn-secondary" onClick={() => { setShowBackendModal(false); setBackendTestMsg(''); }}>
                  Cancel
                </button>
                <button type="button" className="btn btn-primary" onClick={handleTestAndSaveBackend}>
                  Test & Save URL
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: ADD COMPANY */}
        {showNewCompanyModal && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 20 }}>
            <div className="glass-card" style={{ maxWidth: 500, width: '100%', background: 'var(--bg-secondary)' }}>
              <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 16 }}>Initialize New Company</h3>
              <form onSubmit={handleCreateCompany} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Company Name</label>
                  <input
                    type="text"
                    required
                    className="input-field"
                    placeholder="e.g. MeetUniversity, Supabase"
                    value={newCompanyForm.name}
                    onChange={e => setNewCompanyForm({ ...newCompanyForm, name: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Website URL</label>
                  <input
                    type="url"
                    required
                    className="input-field"
                    placeholder="https://..."
                    value={newCompanyForm.website}
                    onChange={e => setNewCompanyForm({ ...newCompanyForm, website: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Initial Context / Notes (Optional)</label>
                  <textarea
                    className="input-field"
                    rows={3}
                    placeholder="Brief description of products or business focus..."
                    value={newCompanyForm.context}
                    onChange={e => setNewCompanyForm({ ...newCompanyForm, context: e.target.value })}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowNewCompanyModal(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={loading}>Initialize Company</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
