import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../../../services/adminService';
import { useAdminRealtime } from '../../../hooks/useAdminRealtime';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await adminService.getStats();
      setStats(data.stats);
      setActivity(data.recent_activity);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleRealtimeEvent = useCallback((event) => {
    console.log("Real-time event received:", event);
    if (event.type === 'ORDER_CREATED' || event.type === 'ORDER_REJECTED') {
      // Refresh stats and activity on new orders or status changes
      fetchDashboardData();
    }
  }, [fetchDashboardData]);

  const { isConnected } = useAdminRealtime(handleRealtimeEvent);

  if (loading) {
    return <div className="admin-dashboard protera-bio-theme">Loading...</div>;
  }

  return (
    <div className="admin-dashboard protera-bio-theme">
      {/* Real-time Status Indicator */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="dot"></span> {isConnected ? 'LIVE' : 'OFFLINE'}
      </div>

      <div className="protera-grid">
        <div className="protera-main-column">
          {/* Grouped Stat Cards with Bio Styling */}
          <div className="bio-stat-row">
            {stats.map((stat, index) => (
              <div key={index} className="bio-stat-card">
                <div className="bio-stat-label">{stat.label}</div>
                <div className="bio-stat-value digital-font">{stat.value}</div>
                <div className="bio-stat-footer text-green">
                  {stat.label === 'PENDING ORDERS' && stat.value > 0 ? 'Priority ↑' : 'Active'}
                </div>
              </div>
            ))}
          </div>

          {/* ... Order Composition Bar ... (kept for visual consistency) */}
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
                <div className="pill-segment color-emerald-light"></div>
                <span className="pill-percentage">18%</span>
              </div>
              <div className="pill-segment-wrapper" style={{ width: '10%' }}>
                <div className="pill-segment color-emerald-dark"></div>
                <span className="pill-percentage">10%</span>
              </div>
            </div>

            <div className="stacked-bar-labels">
              <span><span className="dot color-orange"></span> Completed</span>
              <span><span className="dot color-green-light"></span> Pending (Stock)</span>
              <span><span className="dot color-green-teal"></span> Pending (Review)</span>
              <span><span className="dot color-emerald-light"></span> Processing</span>
              <span><span className="dot color-emerald-dark"></span> Rejected</span>
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
                {activity.map((row) => (
                  <tr key={row.id}>
                    <td className="font-medium text-dark">{row.id}</td>
                    <td>{row.patient}</td>
                    <td>{row.medicine}</td>
                    <td>
                      <span className={`risk-capsule risk-${row.status.toLowerCase() === 'completed' || row.status.toLowerCase() === 'fulfilled' ? 'low' : row.status.toLowerCase() === 'pending' ? 'med' : 'rejected'}`}>
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