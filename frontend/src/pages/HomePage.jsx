import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, BookOpen, AlertCircle } from 'lucide-react';

export default function HomePage() {
  const { login, signup } = useAuth();
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'signup'
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('Username is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }

    if (activeTab === 'signup') {
      if (password.length < 4) {
        setError('Password must be at least 4 characters.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }

    setLoading(true);
    try {
      if (activeTab === 'signup') {
        await signup(username.trim(), password, confirmPassword);
      } else {
        await login(username.trim(), password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing-container">
      <div className="landing-card">
        <div className="landing-logo">M</div>
        <h1 className="landing-title">Meticul</h1>
        <div className="landing-subtitle">Study Planner</div>

        {/* Tab switch */}
        <div className="auth-tab-row">
          <button
            id="tab-login-btn"
            type="button"
            className={`auth-tab-btn ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => { setActiveTab('login'); setError(''); }}
          >
            Log In
          </button>
          <button
            id="tab-signup-btn"
            type="button"
            className={`auth-tab-btn ${activeTab === 'signup' ? 'active' : ''}`}
            onClick={() => { setActiveTab('signup'); setError(''); }}
          >
            Sign Up
          </button>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--danger-bg)',
            color: 'var(--danger-text)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 14px',
            fontSize: '13px',
            marginBottom: '16px',
            textAlign: 'left'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group" style={{ textAlign: 'left' }}>
            <label className="form-label" htmlFor="auth-username">Username</label>
            <input
              id="auth-username"
              type="text"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group" style={{ textAlign: 'left' }}>
            <label className="form-label" htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {activeTab === 'signup' && (
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label className="form-label" htmlFor="auth-confirm-password">Confirm Password</label>
              <input
                id="auth-confirm-password"
                type="password"
                className="form-input"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          <button
            id="auth-submit-btn"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', marginTop: '8px', padding: '11px' }}
          >
            {loading ? 'Please wait...' : (activeTab === 'signup' ? 'Create Account' : 'Log In')}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>
      </div>
    </div>
  );
}
