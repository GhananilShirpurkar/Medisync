import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../../../state/adminStore';
import robogif from '../../../assets/robogif.gif';
import Admin_image from '../../../assets/Admin_image.png';
import './AdminLogin.css';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();

    // Attempt login with the store
    if (adminLogin(username, password)) {
      setError(false);
      navigate('/admin/dashboard');
    } else {
      setError(true);
      setTimeout(() => {
        setError(false);
      }, 2000);
    }
  };

  return (
    <div
      className="admin-login-page"
      style={{
        background: `linear-gradient(135deg, rgba(226, 232, 240, 0.4) 0%, rgba(203, 213, 225, 0.5) 100%), url(${Admin_image})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Background elements */}
      <div className="medical-bg">
        <div className="bokeh bokeh-1"></div>
        <div className="bokeh bokeh-2"></div>
        <div className="bokeh bokeh-3"></div>
        <div className="abstract-line line-1"></div>
        <div className="abstract-line line-2"></div>
      </div>

      <div className="split-login-card">
        {/* Left Side: Video/Character Panel */}
        <div className="login-visual-panel">
          {/* Video Placeholder Container */}
          <div className="video-placeholder">
            <img src={robogif} alt="Medical Mascot" className="mascot-video" />
          </div>

          <div className="visual-overlay">
            <h2 className="visual-heading">Synchronizing Intelligence with Healthcare</h2>
          </div>
        </div>

        {/* Right Side: Form Panel */}
        <div className="login-form-panel">
          <div className="login-form-header">
            <div className="logo-container">
              <span className="logo-icon">💊</span> {/* Placeholder for Yeti icon */}
              <span className="logo-text">MEDISYNC.AI</span>
            </div>
            <h1 className="welcome-heading">WELCOME BACK</h1>
            <p className="welcome-subtext">Enter your username and password to access your account</p>
          </div>

          <form onSubmit={handleSubmit} className="admin-login-form">
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={`form-input ${error ? 'input-error shake' : ''}`}
                autoComplete="username"
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`form-input ${error ? 'input-error shake' : ''}`}
                autoComplete="current-password"
                required
              />
            </div>

            <button type="submit" className="primary-btn" style={{ marginTop: '24px' }}>
              Sign In
            </button>
            {error && <div className="error-message">Invalid credentials</div>}
          </form>
        </div>
      </div>

      {/* Back button */}
      <div className="back-link" onClick={() => navigate('/')}>
        ← Back to home
      </div>
    </div>
  );
};

export default AdminLogin;