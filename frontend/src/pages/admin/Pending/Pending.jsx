import React from 'react';
import './Pending.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const Pending = () => {
  const [orders, setOrders] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [fadingRow, setFadingRow] = React.useState(null);

  React.useEffect(() => {
    const fetchPending = async () => {
      try {
        setLoading(true);
        const data = await adminService.getPendingOrders();
        setOrders(data);
        setError(null);
      } catch (err) {
        console.error('Pending fetch error:', err);
        setError('Failed to load pending orders');
      } finally {
        setLoading(false);
      }
    };
    fetchPending();
  }, []);

  const handleAction = async (id, status) => {
    try {
      setFadingRow(id);
      await adminService.handleOrderAction(id, status);
      
      setTimeout(() => {
        setOrders(prev => prev.filter(order => order.id !== id));
        setFadingRow(null);
      }, 300);
    } catch (err) {
      console.error(`Error ${status}ing order:`, err);
      alert(`Failed to ${status} order. Please try again.`);
      setFadingRow(null);
    }
  };

  if (loading) return <div className="admin-loading">LOADING PENDING ORDERS...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <div className="admin-pending">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">PENDING ORDERS</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      <table className="admin-table pending-table">
        <thead>
          <tr>
            <th>ORDER ID</th>
            <th>PATIENT ID</th>
            <th>WAITING SINCE</th>
            <th>MEDICINES</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr 
              key={order.id} 
              className={fadingRow === order.id ? 'row-fade-out' : ''}
            >
              <td>{order.id}</td>
              <td style={{ color: 'var(--ink-faint)' }}>{order.patient}</td>
              <td style={{ color: 'var(--amber)' }}>{order.waiting}</td>
              <td>{order.medicines}</td>
              <td className="pending-actions">
                <span className="action-approve" onClick={() => handleAction(order.id, 'approved')}>APPROVE</span>
                <span className="action-reject" onClick={() => handleAction(order.id, 'rejected')}>REJECT</span>
              </td>
            </tr>
          ))}
          {orders.length === 0 && (
            <tr>
              <td colSpan="5" className="empty-state">No pending orders at this time.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Pending;
