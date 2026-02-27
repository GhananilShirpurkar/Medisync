import React, { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { pipelineStore } from './state/pipelineStore';
import IdentityPage from './pages/IdentityPage/IdentityPage';
import TheatrePage from './pages/TheatrePage/TheatrePage';
import SummaryPage from './pages/SummaryPage/SummaryPage';

// New Pages
import LandingPage from './pages/LandingPage/LandingPage';
import AdminRouter from './pages/admin/AdminRouter/AdminRouter';
import AdminLogin from './pages/admin/AdminLogin/AdminLogin';
import AdminLayout from './pages/admin/AdminLayout/AdminLayout';
import Dashboard from './pages/admin/Dashboard/Dashboard';
import Inventory from './pages/admin/Inventory/Inventory';
import Customers from './pages/admin/Customers/Customers';
import Orders from './pages/admin/Orders/Orders';
import Pending from './pages/admin/Pending/Pending';

// The original App logic extracted into a sub-component for isolation
const CustomerApp = () => {
  const [pipelineState, setPipelineState] = useState(pipelineStore.get());
  const [displayedPage, setDisplayedPage] = useState(pipelineState.currentPage);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const unsubscribe = pipelineStore.subscribe((newState) => {
      setPipelineState(newState);
      
      // Update body background based on ambientState
      const body = document.body;
      if (newState.ambientState === 'critical') {
        body.style.backgroundColor = 'var(--bg-critical)';
      } else if (newState.ambientState === 'warn') {
        body.style.backgroundColor = 'var(--bg-warn)';
      } else {
        body.style.backgroundColor = 'var(--bg-room)';
      }
    });

    return () => unsubscribe();
  }, []);

  // Handle CSS-driven page transitions
  useEffect(() => {
    if (pipelineState.currentPage !== displayedPage) {
      setIsTransitioning(true);
      // Wait for exit animation (400ms) before swapping component
      setTimeout(() => {
        setDisplayedPage(pipelineState.currentPage);
        setIsTransitioning(false);
      }, 400); 
    }
  }, [pipelineState.currentPage, displayedPage]);

  // Determine transition class
  const getTransitionClass = () => {
    return isTransitioning ? 'page-exit' : 'page-enter';
  };

  const renderPage = () => {
    switch (displayedPage) {
      case 'IDENTITY': return <IdentityPage />;
      case 'THEATRE': return <TheatrePage />;
      case 'SUMMARY': return <SummaryPage />;
      default: return <IdentityPage />;
    }
  };

  return (
    <div className={getTransitionClass()}>
      {renderPage()}
    </div>
  );
};

// Main App Router
const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app/*" element={<CustomerApp />} />
      <Route path="/admin" element={<AdminRouter />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={<AdminLayout><Dashboard /></AdminLayout>} />
      <Route path="/admin/inventory" element={<AdminLayout><Inventory /></AdminLayout>} />
      <Route path="/admin/customers" element={<AdminLayout><Customers /></AdminLayout>} />
      <Route path="/admin/orders" element={<AdminLayout><Orders /></AdminLayout>} />
      <Route path="/admin/pending" element={<AdminLayout><Pending /></AdminLayout>} />
    </Routes>
  );
};

export default App;
