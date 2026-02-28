import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Users, Package, ShoppingCart, Activity, ShieldCheck, Database,
  Search, Bell, Settings, Filter, Download
} from 'lucide-react';
import { adminLogout, adminState } from '../../../state/adminStore';
import logoImage from '../../../assets/logo.jpeg';
import './AdminLayout.css';

const AdminLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    adminLogout();
    navigate('/');
  };

  const navItems = [
    { label: 'Dashboard', path: '/admin/dashboard', icon: '⧉' },
    { label: 'Inventory', path: '/admin/inventory', icon: '📁' },
    { label: 'Customers', path: '/admin/customers', icon: '👥' },
    { label: 'Orders', path: '/admin/orders', icon: '📦' },
    { label: 'Pending', path: '/admin/pending', icon: '⏳' },
  ];

  const currentPage = navItems.find(item => item.path === location.pathname);
  const pageTitle = currentPage?.label || 'Admin';
  const isDashboard = location.pathname === '/admin/dashboard';
  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <div className="admin-layout protera-bio-theme">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <div className="admin-logo-group" onClick={() => navigate('/')}>
            <div className="admin-logo-img-wrapper">
              <img src={logoImage} alt="MediSync" className="admin-logo-img" />
            </div>
            <span className="admin-logo-text">MEDISYNC</span>
          </div>
        </div>

        <div className="admin-user-profile">
          <img src={`https://ui-avatars.com/api/?name=${adminState.adminUser || 'Admin'}&background=3b82f6&color=fff`} alt="User" className="user-avatar" />
          <div className="user-info">
            <span className="user-name">{adminState.adminUser || 'Admin'}</span>
          </div>
        </div>

        <nav className="admin-nav">
          <div className="nav-group">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  isActive ? 'admin-nav-item active' : 'admin-nav-item'
                }
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>

          <div className="nav-footer-group">
            <button className="admin-signout" onClick={handleLogout}>
              <span className="nav-icon logout-icon">←</span> Log out
            </button>
          </div>
        </nav>
      </aside>

      <main className="admin-content">
        <header className="admin-main-header">
          <div className="header-page-title">
            <h1 className="admin-page-title">{pageTitle.toUpperCase()}</h1>
            <p className="admin-page-subtitle">{today}</p>
          </div>

          <div className="header-right">
            {!isDashboard && (
              <div className="admin-header-search">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  placeholder={`Search ${pageTitle}...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            )}
            <button className="icon-btn">🔔</button>
          </div>
        </header>

        <div className="page-content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;