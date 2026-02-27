import React from 'react';
import './Inventory.css';
import { adminState } from '../../../state/adminStore';
import { adminService } from '../../../services/adminService';

const Inventory = () => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [inventory, setInventory] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchInventory = async () => {
      try {
        setLoading(true);
        const data = await adminService.getInventory();
        setInventory(data);
        setError(null);
      } catch (err) {
        console.error('Inventory fetch error:', err);
        setError('Failed to load inventory');
      } finally {
        setLoading(false);
      }
    };
    fetchInventory();
  }, []);

  const today = new Date().toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  const filteredInventory = inventory.filter(item => 
    (item.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (item.category || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="admin-loading">LOADING INVENTORY...</div>;
  if (error) return <div className="admin-error">{error}</div>;

  const renderStock = (stock) => {
    if (stock < 10) {
      return <span className="stock-critical">{stock} <span className="stock-label">LOW</span></span>;
    } else if (stock <= 30) {
      return <span className="stock-warn">{stock}</span>;
    }
    return <span className="stock-good">{stock}</span>;
  };

  return (
    <div className="admin-inventory">
      <div className="admin-page-header">
        <div className="admin-page-title-row">
          <h1 className="admin-page-title">INVENTORY</h1>
          <span className="admin-user">{adminState.adminUser || 'admin'}</span>
        </div>
        <div className="admin-page-date">{today}</div>
      </div>

      <div className="admin-search-bar">
        <input 
          type="text" 
          placeholder="Search medicines..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>MEDICINE NAME</th>
            <th>CATEGORY</th>
            <th>STOCK</th>
            <th>UNIT PRICE</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {filteredInventory.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td style={{ color: 'var(--ink-faint)' }}>{item.category}</td>
              <td>{renderStock(item.stock)}</td>
              <td>{item.price}</td>
              <td style={{ fontSize: '9px' }}>{item.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Inventory;
