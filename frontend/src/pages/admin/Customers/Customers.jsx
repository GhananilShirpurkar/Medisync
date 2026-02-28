import React, { useState, useEffect } from 'react';
import { useAdminContext } from '../../../context/AdminContext';

const Customers = () => {
  const { searchQuery } = useAdminContext();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRiskSummary = async () => {
      try {
        const response = await fetch('/api/conversation/admin/risk-summary');
        const data = await response.json();
        setCustomers(data);
      } catch (error) {
        console.error('Failed to fetch risk summary:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRiskSummary();
  }, []);

  const filteredCustomers = customers.filter(customer =>
    (customer.pid?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  const getRiskBadgeStyle = (level) => {
    switch (level) {
      case 'critical':
        return { backgroundColor: '#000000', color: '#ffffff', fontWeight: 'bold' };
      case 'high':
        return { backgroundColor: '#ef4444', color: '#ffffff' };
      case 'elevated':
        return { backgroundColor: '#f97316', color: '#ffffff' };
      default:
        return { backgroundColor: '#22c55e', color: '#ffffff' };
    }
  };

  return (
    <div className="admin-customers protera-theme">
      <div className="protera-main-column">
        <div className="protera-table-card">
          <h3 className="card-title">Patient Risk Records</h3>

          {loading ? (
            <div style={{ padding: '20px', textAlign: 'center' }}>Loading risk profiles...</div>
          ) : (
            <table className="protera-table">
              <thead>
                <tr>
                  <th>PATIENT ID</th>
                  <th>RISK LEVEL</th>
                  <th>SCORE</th>
                  <th>LAST UPDATED</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer) => (
                  <tr key={customer.pid}>
                    <td className="font-medium text-dark">{customer.pid}</td>
                    <td>
                      <span 
                        className="px-2 py-1 rounded-full text-xs uppercase"
                        style={getRiskBadgeStyle(customer.risk_level)}
                      >
                        {customer.risk_level}
                      </span>
                    </td>
                    <td>{customer.risk_score}/100</td>
                    <td style={{ color: '#6b7280', fontSize: '12px' }}>
                      {customer.updated_at ? new Date(customer.updated_at).toLocaleString() : 'Never'}
                    </td>
                    <td>
                        {customer.flagged ? (
                            <span className="text-red-600 font-bold text-xs">🚩 FLAGGED</span>
                        ) : (
                            <span className="text-green-600 text-xs">NORMAL</span>
                        )}
                    </td>
                  </tr>
                ))}
                {filteredCustomers.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
                      No risk profiles found. Use the pharmacy to generate data.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default Customers;