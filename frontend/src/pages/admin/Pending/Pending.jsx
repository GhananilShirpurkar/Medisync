import React, { useState, useEffect } from 'react';
import './Pending.css';

const initialPendingOrders = [
  { id: 'ORD-892B', patient: 'PAT-4933', waiting: '2h 14m', medicines: 'Lisinopril 10mg (2x)' },
  { id: 'ORD-892E', patient: 'PAT-4928', waiting: '1h 45m', medicines: 'Levothyroxine 50mcg (1x)' },
  { id: 'ORD-891H', patient: 'PAT-4927', waiting: '5h 10m', medicines: 'Azithromycin 250mg (1x)' },
  { id: 'ORD-890M', patient: 'PAT-4923', waiting: '1d 2h', medicines: 'Sertraline 50mg (1x)' },
  { id: 'ORD-892F', patient: 'PAT-4911', waiting: '45m', medicines: 'Amoxicillin 500mg (1x)' },
  { id: 'ORD-891X', patient: 'PAT-4940', waiting: '3h 20m', medicines: 'Omeprazole 20mg (3x)' },
  { id: 'ORD-889P', patient: 'PAT-4902', waiting: '1d 6h', medicines: 'Amlodipine 5mg (2x)' },
  { id: 'ORD-892G', patient: 'PAT-4918', waiting: '12m', medicines: 'Ibuprofen 400mg (1x)' }
];

const Pending = () => {
  const [activeTab, setActiveTab] = useState('orders'); // 'orders' | 'risk'
  const [orders, setOrders] = useState(initialPendingOrders);
  const [riskFlags, setRiskFlags] = useState([]);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [fadingRow, setFadingRow] = useState(null);

  useEffect(() => {
    if (activeTab === 'risk') {
      fetchRiskFlags();
    }
  }, [activeTab]);

  const fetchRiskFlags = async () => {
    setLoadingRisk(true);
    try {
      const response = await fetch('/api/conversation/admin/risk-summary');
      const data = await response.json();
      // Filter for elevated or higher
      const flagged = data.filter(p => p.risk_level !== 'normal');
      setRiskFlags(flagged);
    } catch (error) {
      console.error('Failed to fetch risk flags:', error);
    } finally {
      setLoadingRisk(false);
    }
  };

  const handleAction = (id) => {
    setFadingRow(id);
    setTimeout(() => {
      setOrders(orders.filter(order => order.id !== id));
      setFadingRow(null);
    }, 300);
  };

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'critical': return { bg: '#000', text: '#fff' };
      case 'high': return { bg: '#ef4444', text: '#fff' };
      default: return { bg: '#f97316', text: '#fff' };
    }
  };

  return (
    <div className="admin-pending protera-theme">
      <div className="protera-main-column">
        <div className="protera-tabs">
          <div 
            className={`tab-item ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            PENDING ORDERS
          </div>
          <div 
            className={`tab-item ${activeTab === 'risk' ? 'active' : ''}`}
            onClick={() => setActiveTab('risk')}
          >
            RISK FLAGS {riskFlags.length > 0 && <span className="risk-count">{riskFlags.length}</span>}
          </div>
        </div>

        <div className="protera-table-card">
          <h3 className="card-title">
            {activeTab === 'orders' ? 'Pending Approval' : 'Behavioral Risk Flags'}
          </h3>

          <table className="protera-table">
            {activeTab === 'orders' ? (
              <>
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
                    <tr key={order.id} className={fadingRow === order.id ? 'row-fade-out' : ''}>
                      <td className="font-medium text-dark">{order.id}</td>
                      <td style={{ color: '#6b7280' }}>{order.patient}</td>
                      <td style={{ color: '#f59e0b', fontWeight: '600' }}>{order.waiting}</td>
                      <td>{order.medicines}</td>
                      <td className="pending-actions">
                        <span className="action-approve" onClick={() => handleAction(order.id)}>APPROVE</span>
                        <span className="action-reject" onClick={() => handleAction(order.id)}>REJECT</span>
                      </td>
                    </tr>
                  ))}
                  {orders.length === 0 && (
                    <tr><td colSpan="5" className="empty-state">No pending orders.</td></tr>
                  )}
                </tbody>
              </>
            ) : (
              <>
                <thead>
                  <tr>
                    <th>PATIENT ID</th>
                    <th>SCORE</th>
                    <th>LEVEL</th>
                    <th>FLAGS</th>
                    <th>UPDATED</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingRisk ? (
                    <tr><td colSpan="5" className="empty-state">Loading risk profiles...</td></tr>
                  ) : riskFlags.length > 0 ? (
                    riskFlags.map((risk) => (
                      <tr key={risk.pid}>
                        <td className="font-medium text-dark">{risk.pid}</td>
                        <td className="font-bold">{risk.risk_score}</td>
                        <td>
                          <span 
                            className="risk-badge" 
                            style={{ 
                              backgroundColor: getRiskBadgeColor(risk.risk_level).bg,
                              color: getRiskBadgeColor(risk.risk_level).text
                            }}
                          >
                            {risk.risk_level}
                          </span>
                        </td>
                        <td style={{ fontSize: '11px', maxWidth: '300px' }}>
                          <div className="flex flex-wrap gap-1">
                            {risk.risk_flags.map((f, i) => (
                              <span key={i} className="bg-slate-100 text-slate-600 px-1 rounded border">
                                {f}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td style={{ color: '#6b7280', fontSize: '11px' }}>
                          {new Date(risk.updated_at).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="5" className="empty-state">No high-risk patients detected.</td></tr>
                  )}
                </tbody>
              </>
            )}
          </table>
        </div>
      </div>
    </div>
  );
};

export default Pending;