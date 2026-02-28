import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const AdminContext = createContext();

export const AdminProvider = ({ children }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const location = useLocation();

  // Reset search when navigating between admin pages
  useEffect(() => {
    setSearchQuery('');
  }, [location.pathname]);

  return (
    <AdminContext.Provider value={{ searchQuery, setSearchQuery }}>
      {children}
    </AdminContext.Provider>
  );
};

export const useAdminContext = () => {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error('useAdminContext must be used within an AdminProvider');
  }
  return context;
};
