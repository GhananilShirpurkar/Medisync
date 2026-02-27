import React from 'react';
import './Customers.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const Customers = () => {
  const [customers, setCustomers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchCustomers = async () => {
      try {
        setLoading(true);
        const data = await adminService.getCustomers();
        setCustomers(data);
        setError(null);
      } catch (err) {
        console.error('Customers fetch error:', err);
        setError('Failed to load customers');
      } finally {
        setLoading(false);
      }
    };
    fetchCustomers();
  }, []);

  if (loading) return <div className="admin-loading">LOADING CUSTOMERS...</div>;
  if (error) return <div className="admin-error">{error}</div>;
  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  return (
    <div className="admin-customers">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">CUSTOMERS</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>PATIENT ID</th>
            <th>PHONE</th>
            <th>REGISTERED</th>
            <th>TOTAL ORDERS</th>
            <th>LAST VISIT</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={customer.id}>
              <td>{customer.id}</td>
              <td style={{ color: 'var(--ink-faint)' }}>{customer.phone}</td>
              <td>{customer.registered}</td>
              <td>{customer.orders}</td>
              <td>{customer.lastVisit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Customers;
