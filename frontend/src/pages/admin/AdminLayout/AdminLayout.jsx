import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { adminLogout } from '../../../state/adminStore';
import './AdminLayout.css';

const AdminLayout = ({ children }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    adminLogout();
    navigate('/');
  };

  const navItems = [
    { label: 'DASHBOARD', path: '/admin/dashboard' },
    { label: 'INVENTORY', path: '/admin/inventory' },
    { label: 'CUSTOMERS', path: '/admin/customers' },
    { label: 'ORDERS', path: '/admin/orders' },
    { label: 'PENDING', path: '/admin/pending' }
  ];

  return (
    <div className="admin-layout">
      {/* Sidebar */}
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <div className="admin-logo">MEDISYNC</div>
          <div className="admin-subtitle">ADMIN</div>
        </div>
        
        <nav className="admin-nav">
          {navItems.map((item) => (
            <NavLink 
              key={item.path}
              to={item.path} 
              className={({ isActive }) => 
                isActive ? 'admin-nav-item active' : 'admin-nav-item'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        
        <div className="admin-sidebar-footer">
          <button className="admin-signout" onClick={handleLogout}>
            SIGN OUT
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="admin-content">
        {children}
      </main>
    </div>
  );
};

export default AdminLayout;
