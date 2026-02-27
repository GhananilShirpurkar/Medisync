import React from 'react';
import './Orders.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const Orders = () => {
  const [orders, setOrders] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const data = await adminService.getOrders();
        setOrders(data);
        setError(null);
      } catch (err) {
        console.error('Orders fetch error:', err);
        setError('Failed to load orders');
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);

  if (loading) return <div className="admin-loading">LOADING ORDERS...</div>;
  if (error) return <div className="admin-error">{error}</div>;
  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <div className="admin-orders">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">ORDERS</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>ORDER ID</th>
            <th>PATIENT ID</th>
            <th>MEDICINES</th>
            <th>TOTAL</th>
            <th>STATUS</th>
            <th>DATE</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>{order.id}</td>
              <td style={{ color: 'var(--ink-faint)' }}>{order.patient}</td>
              <td>{order.medicines}</td>
              <td>{order.total}</td>
              <td className={`status-${order.status.toLowerCase()}`}>{order.status}</td>
              <td>{order.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Orders;
