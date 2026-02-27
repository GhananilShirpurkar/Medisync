import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAdminAuthenticated } from '../../../state/adminStore';

const AdminRouter = () => {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAdminAuthenticated()) {
      navigate('/admin/dashboard', { replace: true });
    } else {
      navigate('/admin/login', { replace: true });
    }
  }, [navigate]);

  return null; // The router just redirects
};

export default AdminRouter;
