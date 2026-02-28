import React from 'react';
import './Dashboard.css';

const Dashboard = () => {

  const mockActivity = [
    { id: 'ORD-892A', patient: 'Elena Rostova', medicine: 'Amoxicillin 500mg', status: 'COMPLETED', time: '10:42 AM' },
    { id: 'ORD-892B', patient: 'Marcus Chen', medicine: 'Lisinopril 10mg', status: 'PENDING', time: '11:15 AM' },
    { id: 'ORD-892C', patient: 'Sarah Jenkins', medicine: 'Metformin 850mg', status: 'COMPLETED', time: '11:30 AM' },
    { id: 'ORD-892D', patient: 'David Okafor', medicine: 'Atorvastatin 20mg', status: 'REJECTED', time: '12:05 PM' },
    { id: 'ORD-892E', patient: 'Priya Sharma', medicine: 'Levothyroxine 50mcg', status: 'PENDING', time: '12:45 PM' }
  ];

  return (
    <div className="admin-dashboard protera-bio-theme">
      <div className="protera-grid">
        <div className="protera-main-column">
          {/* Grouped Stat Cards with Bio Styling */}
          <div className="bio-stat-row">
            <div className="bio-stat-card">
              <div className="bio-stat-label">TOTAL ORDERS</div>
              <div className="bio-stat-value digital-font">142</div>
              <div className="bio-stat-footer text-green">+12% ↑</div>
            </div>
            <div className="bio-stat-card">
              <div className="bio-stat-label">PENDING ORDERS</div>
              <div className="bio-stat-value digital-font">7</div>
              <div className="bio-stat-footer text-green">Priority ↑</div>
            </div>
            <div className="bio-stat-card">
              <div className="bio-stat-label">LOW STOCK</div>
              <div className="bio-stat-value digital-font">4</div>
              <div className="bio-stat-footer text-green">Critical ↓</div>
            </div>
          </div>

          {/* Order Composition Bar */}
          <div className="protera-composition-card">
            <div className="card-header-flex">
              <h1 className="card-title">Order Composition</h1>
            </div>

            <div className="segmented-pill-container">
              <div className="pill-segment-wrapper" style={{ width: '30%' }}>
                <div className="pill-segment color-orange"></div>
                <span className="pill-percentage">30%</span>
              </div>
              <div className="pill-segment-wrapper" style={{ width: '22%' }}>
                <div className="pill-segment color-green-light"></div>
                <span className="pill-percentage">22%</span>
              </div>
              <div className="pill-segment-wrapper" style={{ width: '20%' }}>
                <div className="pill-segment color-green-teal"></div>
                <span className="pill-percentage">20%</span>
              </div>
              <div className="pill-segment-wrapper" style={{ width: '18%' }}>
                <div className="pill-segment color-purple-light"></div>
                <span className="pill-percentage">18%</span>
              </div>
              <div className="pill-segment-wrapper" style={{ width: '10%' }}>
                <div className="pill-segment color-purple-dark"></div>
                <span className="pill-percentage">10%</span>
              </div>
            </div>

            <div className="stacked-bar-labels">
              <span><span className="dot color-orange"></span> Completed</span>
              <span><span className="dot color-green-light"></span> Pending (Stock)</span>
              <span><span className="dot color-green-teal"></span> Pending (Review)</span>
              <span><span className="dot color-purple-light"></span> Processing</span>
              <span><span className="dot color-purple-dark"></span> Rejected</span>
            </div>
          </div>

          {/* Activity Table */}
          <div className="protera-table-card">
            <h3 className="card-title">Recent Activity</h3>
            <table className="protera-table bio-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Patient</th>
                  <th>Medicine</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {mockActivity.map((row) => (
                  <tr key={row.id}>
                    <td className="font-medium text-dark">{row.id}</td>
                    <td>{row.patient}</td>
                    <td>{row.medicine}</td>
                    <td>
                      <span className={`risk-capsule risk-${row.status === 'COMPLETED' ? 'low' : row.status === 'PENDING' ? 'med' : 'rejected'}`}>
                        {row.status}
                      </span>
                    </td>
                    <td>{row.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;