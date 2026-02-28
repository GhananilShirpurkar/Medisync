import React from 'react';
import './Orders.css';

const mockOrders = [
  { id: 'ORD-892A', patient: 'PAT-4921', medicines: 'Amoxicillin 500mg (1x)', total: '$14.50', status: 'COMPLETED', date: 'Feb 24, 2026' },
  { id: 'ORD-892B', patient: 'PAT-4933', medicines: 'Lisinopril 10mg (2x)', total: '$8.20', status: 'PENDING', date: 'Feb 24, 2026' },
  { id: 'ORD-892C', patient: 'PAT-4925', medicines: 'Metformin 850mg (1x)', total: '$5.00', status: 'COMPLETED', date: 'Feb 24, 2026' },
  { id: 'ORD-892D', patient: 'PAT-4922', medicines: 'Atorvastatin 20mg (3x)', total: '$21.60', status: 'REJECTED', date: 'Feb 24, 2026' },
  { id: 'ORD-892E', patient: 'PAT-4928', medicines: 'Levothyroxine 50mcg (1x)', total: '$11.00', status: 'PENDING', date: 'Feb 24, 2026' },
  { id: 'ORD-891F', patient: 'PAT-4924', medicines: 'Omeprazole 20mg (2x)', total: '$14.00', status: 'COMPLETED', date: 'Feb 23, 2026' },
  { id: 'ORD-891G', patient: 'PAT-4931', medicines: 'Amlodipine 5mg (1x)', total: '$6.50', status: 'COMPLETED', date: 'Feb 23, 2026' },
  { id: 'ORD-891H', patient: 'PAT-4927', medicines: 'Azithromycin 250mg (1x)', total: '$18.00', status: 'PENDING', date: 'Feb 23, 2026' },
  { id: 'ORD-891I', patient: 'PAT-4929', medicines: 'Losartan 50mg (1x)', total: '$9.20', status: 'COMPLETED', date: 'Feb 23, 2026' },
  { id: 'ORD-891J', patient: 'PAT-4935', medicines: 'Albuterol Inhaler (1x)', total: '$24.50', status: 'REJECTED', date: 'Feb 23, 2026' },
  { id: 'ORD-890K', patient: 'PAT-4926', medicines: 'Gabapentin 300mg (2x)', total: '$18.40', status: 'COMPLETED', date: 'Feb 22, 2026' },
  { id: 'ORD-890L', patient: 'PAT-4934', medicines: 'Hydrochlorothiazide 25mg (1x)', total: '$4.10', status: 'COMPLETED', date: 'Feb 22, 2026' },
  { id: 'ORD-890M', patient: 'PAT-4923', medicines: 'Sertraline 50mg (1x)', total: '$12.00', status: 'PENDING', date: 'Feb 22, 2026' },
  { id: 'ORD-890N', patient: 'PAT-4932', medicines: 'Montelukast 10mg (1x)', total: '$16.50', status: 'COMPLETED', date: 'Feb 22, 2026' },
  { id: 'ORD-890O', patient: 'PAT-4930', medicines: 'Fluticasone Nasal Spray (1x)', total: '$18.00', status: 'COMPLETED', date: 'Feb 21, 2026' }
];

const Orders = () => {
  return (
    <div className="admin-orders protera-theme">
      <div className="protera-main-column">
        <div className="protera-table-card">
          <h3 className="card-title">Order History</h3>

          <table className="protera-table">
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
              {mockOrders.map((order) => (
                <tr key={order.id}>
                  <td className="font-medium text-dark">{order.id}</td>
                  <td style={{ color: '#6b7280' }}>{order.patient}</td>
                  <td>{order.medicines}</td>
                  <td>{order.total}</td>
                  <td>
                    <span className={`risk-pill risk-${order.status.toLowerCase()}`}>
                      <span className="risk-dot"></span> {order.status}
                    </span>
                  </td>
                  <td>{order.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Orders;