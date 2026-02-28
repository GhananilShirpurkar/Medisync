import React, { useState } from 'react';
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
  const [orders, setOrders] = useState(initialPendingOrders);
  const [fadingRow, setFadingRow] = useState(null);

  const handleAction = (id) => {
    setFadingRow(id);
    setTimeout(() => {
      setOrders(orders.filter(order => order.id !== id));
      setFadingRow(null);
    }, 300);
  };

  return (
    <div className="admin-pending protera-theme">
      <div className="protera-main-column">
        <div className="protera-table-card">
          <h3 className="card-title">Pending Approval</h3>

          <table className="protera-table pending-table">
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
                <tr>
                  <td colSpan="5" className="empty-state">
                    No pending orders at this time.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Pending;