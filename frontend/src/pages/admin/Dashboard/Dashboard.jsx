import React from 'react';
import './Dashboard.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const Dashboard = () => {
  const [data, setData] = React.useState({ stats: [], recent_activity: [] });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await adminService.getStats();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="admin-loading">LOADING DASHBOARD...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  const { stats, recent_activity } = data;

  return (
    <div className="admin-dashboard">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">DASHBOARD</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      <div className="dashboard-stats-grid">
        {stats.map((stat, index) => (
          <div className="stat-card" key={index}>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="dashboard-activity">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ORDER ID</th>
              <th>PATIENT</th>
              <th>MEDICINE</th>
              <th>STATUS</th>
              <th>TIME</th>
            </tr>
          </thead>
          <tbody>
            {recent_activity.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.patient}</td>
                <td>{row.medicine}</td>
                <td className={`status-${row.status.toLowerCase()}`}>{row.status}</td>
                <td>{row.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
