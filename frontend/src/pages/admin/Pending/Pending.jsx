import React from 'react';
import './Pending.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const URGENCY_COLOR = {
  urgent: 'var(--red, #e53e3e)',
  soon:   'var(--amber, #d69e2e)',
  normal: 'var(--green, #38a169)',
};

const Pending = () => {
  const [activeTab, setActiveTab] = React.useState('orders');

  // ── Pending Orders state ──────────────────────────────────────────
  const [orders, setOrders]       = React.useState([]);
  const [ordersLoading, setOrdersLoading] = React.useState(true);
  const [ordersError, setOrdersError]     = React.useState(null);
  const [fadingRow, setFadingRow] = React.useState(null);

  // ── Refill Alerts state ───────────────────────────────────────────
  const [alerts, setAlerts]         = React.useState([]);
  const [alertsLoading, setAlertsLoading] = React.useState(false);
  const [alertsError, setAlertsError]     = React.useState(null);
  const [sentAlerts, setSentAlerts] = React.useState(new Set());

  // ── Fetch pending orders ──────────────────────────────────────────
  React.useEffect(() => {
    const fetchPending = async () => {
      try {
        setOrdersLoading(true);
        const data = await adminService.getPendingOrders();
        setOrders(data);
        setOrdersError(null);
      } catch (err) {
        console.error('Pending fetch error:', err);
        setOrdersError('Failed to load pending orders');
      } finally {
        setOrdersLoading(false);
      }
    };
    fetchPending();
  }, []);

  // ── Fetch refill alerts when tab opens ────────────────────────────
  React.useEffect(() => {
    if (activeTab !== 'refills') return;
    const fetchAlerts = async () => {
      try {
        setAlertsLoading(true);
        const res = await fetch(`${API_BASE}/api/v1/admin/refill-alerts`);
        const data = await res.json();
        setAlerts(data.alerts || []);
        setAlertsError(null);
      } catch (err) {
        console.error('Refill alerts fetch error:', err);
        setAlertsError('Failed to load refill alerts');
      } finally {
        setAlertsLoading(false);
      }
    };
    fetchAlerts();
  }, [activeTab]);

  // ── Handlers ──────────────────────────────────────────────────────
  const handleOrderAction = async (id, status) => {
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

  const handleSendAlert = async (userId, medicineName) => {
    const key = `${userId}__${medicineName}`;
    try {
      await fetch(`${API_BASE}/api/v1/admin/send-refill-alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, medicine_name: medicineName }),
      });
      setSentAlerts(prev => new Set([...prev, key]));
    } catch (err) {
      console.error('Send alert error:', err);
      alert('Failed to send alert. Please try again.');
    }
  };

  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  return (
    <div className="admin-pending">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">ORDERS &amp; REFILLS</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      {/* Tab bar */}
      <div className="pending-tabs">
        <button
          className={`pending-tab${activeTab === 'orders' ? ' active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          PENDING ORDERS
        </button>
        <button
          className={`pending-tab${activeTab === 'refills' ? ' active' : ''}`}
          onClick={() => setActiveTab('refills')}
        >
          REFILL ALERTS
        </button>
      </div>

      {/* ── Pending Orders Tab ─────────────────────────────────────── */}
      {activeTab === 'orders' && (
        <>
          {ordersLoading && <div className="admin-loading">LOADING PENDING ORDERS...</div>}
          {ordersError  && <div className="admin-error">{ordersError}</div>}
          {!ordersLoading && !ordersError && (
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
                {orders.map(order => (
                  <tr key={order.id} className={fadingRow === order.id ? 'row-fade-out' : ''}>
                    <td>{order.id}</td>
                    <td style={{ color: 'var(--ink-faint)' }}>{order.patient}</td>
                    <td style={{ color: 'var(--amber)' }}>{order.waiting}</td>
                    <td>{order.medicines}</td>
                    <td className="pending-actions">
                      <span className="action-approve" onClick={() => handleOrderAction(order.id, 'approved')}>APPROVE</span>
                      <span className="action-reject"  onClick={() => handleOrderAction(order.id, 'rejected')}>REJECT</span>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr><td colSpan="5" className="empty-state">No pending orders at this time.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* ── Refill Alerts Tab ──────────────────────────────────────── */}
      {activeTab === 'refills' && (
        <>
          {alertsLoading && <div className="admin-loading">LOADING REFILL ALERTS...</div>}
          {alertsError  && <div className="admin-error">{alertsError}</div>}
          {!alertsLoading && !alertsError && (
            <table className="admin-table pending-table">
              <thead>
                <tr>
                  <th>PATIENT ID</th>
                  <th>MEDICINE</th>
                  <th>DEPLETES IN</th>
                  <th>URGENCY</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map(alert => {
                  const key = `${alert.user_id}__${alert.medicine_name}`;
                  const sent = sentAlerts.has(key);
                  return (
                    <tr
                      key={key}
                      style={{ opacity: sent ? 0.4 : 1, transition: 'opacity 0.3s' }}
                    >
                      <td style={{ color: 'var(--ink-faint)' }}>{alert.user_id}</td>
                      <td>{alert.medicine_name}</td>
                      <td style={{ color: URGENCY_COLOR[alert.urgency] }}>
                        {alert.days_until_depletion < 0 ? 'OVERDUE' : `${alert.days_until_depletion}d`}
                      </td>
                      <td style={{ color: URGENCY_COLOR[alert.urgency], fontWeight: 600 }}>
                        {alert.urgency.toUpperCase()}
                      </td>
                      <td>
                        {sent ? (
                          <span style={{ color: 'var(--green, #38a169)' }}>SENT ✓</span>
                        ) : (
                          <span
                            className="action-approve"
                            onClick={() => handleSendAlert(alert.user_id, alert.medicine_name)}
                          >
                            SEND ALERT
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {alerts.length === 0 && (
                  <tr><td colSpan="5" className="empty-state">No refill alerts at this time.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
};

export default Pending;
