import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../../../state/adminStore';
import './AdminLogin.css';

const AdminLogin = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (adminLogin(username, password)) {
      setError(false);
      navigate('/admin/dashboard');
    } else {
      setError(true);
      // Remove error after 2s
      setTimeout(() => {
        setError(false);
      }, 2000);
    }
  };

  return (
    <div className="admin-login-page">
      <div className="admin-login-card">
        <h1 className="admin-login-title">MEDISYNC ADMIN</h1>
        
        <form onSubmit={handleSubmit} className="admin-login-form">
          <div className="admin-login-field">
            <label>Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={error ? 'shake' : ''}
              autoComplete="username"
            />
          </div>
          
          <div className="admin-login-field">
            <label>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={error ? 'shake' : ''}
              autoComplete="current-password"
            />
          </div>
          
          <div className="admin-login-submit-wrapper">
            <button type="submit" className="admin-login-submit">
              [ SIGN IN ]
            </button>
            {error && <div className="admin-login-error">Invalid credentials</div>}
          </div>
        </form>
        
        <div className="admin-login-back" onClick={() => navigate('/')}>
          ← Back to home
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
