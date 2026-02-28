import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../../../services/adminService';
import { useAdminRealtime } from '../../../hooks/useAdminRealtime';
import './Inventory.css';
import { useAdminContext } from '../../../context/AdminContext';

const Inventory = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { searchQuery } = useAdminContext();
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    price: 0,
    stock: 0,
    requires_prescription: false
  });

  const filteredInventory = inventory.filter(item => 
    (item.name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (item.category?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  const fetchInventory = useCallback(async () => {
    try {
      const data = await adminService.getInventory();
      setInventory(data);
    } catch (err) {
      console.error("Failed to fetch inventory:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const handleRealtimeEvent = useCallback((event) => {
    if (event.type === 'STOCK_UPDATED') {
      fetchInventory();
    }
  }, [fetchInventory]);

  useAdminRealtime(handleRealtimeEvent);

  const handleOpenModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        name: item.name,
        category: item.category,
        price: parseFloat(item.price.replace('$', '')),
        stock: item.stock,
        requires_prescription: item.requires_prescription || false
      });
    } else {
      setEditingItem(null);
      setFormData({
        name: '',
        category: '',
        price: 0,
        stock: 0,
        requires_prescription: false
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingItem(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await adminService.updateMedicine(editingItem.id, formData);
      } else {
        await adminService.addMedicine(formData);
      }
      handleCloseModal();
      fetchInventory();
    } catch (err) {
      alert("Failed to save medicine: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this medicine?")) {
      try {
        await adminService.deleteMedicine(id);
        fetchInventory();
      } catch (err) {
        alert("Failed to delete medicine: " + err.message);
      }
    }
  };

  const renderStock = (stock) => {
    if (stock < 10) {
      return <span className="stock-critical">{stock} <span className="stock-label">LOW</span></span>;
    } else if (stock <= 30) {
      return <span className="stock-warn">{stock}</span>;
    }
    return <span className="stock-good">{stock}</span>;
  };

  if (loading) {
    return <div className="admin-inventory protera-theme">Loading...</div>;
  }

  return (
    <div className="admin-inventory protera-theme">
      <div className="protera-main-column">
        <div className="inventory-header-actions">
           <button className="protera-btn protera-btn-primary" onClick={() => handleOpenModal()}>
             + Add New Medicine
           </button>
        </div>

        <div className="protera-table-card">
          <h3 className="card-title">Medicine Stock</h3>

          <table className="protera-table">
            <thead>
              <tr>
                <th>MEDICINE NAME</th>
                <th>CATEGORY</th>
                <th>STOCK</th>
                <th>UNIT PRICE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredInventory.map((item) => (
                <tr key={item.id}>
                  <td className="font-medium text-dark">{item.name}</td>
                  <td style={{ color: '#6b7280' }}>{item.category}</td>
                  <td>{renderStock(item.stock)}</td>
                  <td>{item.price}</td>
                  <td>
                    <span className={`risk-pill risk-${item.status.toLowerCase().replace(/\s+/g, '.')}`}>
                      <span className="risk-dot"></span> {item.status}
                    </span>
                  </td>
                  <td className="table-actions">
                    <button className="action-link edit" onClick={() => handleOpenModal(item)}>Edit</button>
                    <button className="action-link delete" onClick={() => handleDelete(item.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="admin-modal-overlay">
          <div className="admin-modal">
            <div className="modal-header">
              <h3>{editingItem ? 'Edit Medicine' : 'Add New Medicine'}</h3>
              <button className="close-btn" onClick={handleCloseModal}>×</button>
            </div>
            <form onSubmit={handleSubmit} className="admin-form">
              <div className="form-group">
                <label>Medicine Name</label>
                <input 
                  type="text" 
                  value={formData.name} 
                  onChange={(e) => setFormData({...formData, name: e.target.value})} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <input 
                  type="text" 
                  value={formData.category} 
                  onChange={(e) => setFormData({...formData, category: e.target.value})} 
                  required 
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price ($)</label>
                  <input 
                    type="number" 
                    step="0.01" 
                    value={formData.price} 
                    onChange={(e) => setFormData({...formData, price: parseFloat(e.target.value)})} 
                    required 
                  />
                </div>
                <div className="form-group">
                  <label>Stock</label>
                  <input 
                    type="number" 
                    value={formData.stock} 
                    onChange={(e) => setFormData({...formData, stock: parseInt(e.target.value)})} 
                    required 
                  />
                </div>
              </div>
              <div className="form-group checkbox-group">
                <label>
                  <input 
                    type="checkbox" 
                    checked={formData.requires_prescription} 
                    onChange={(e) => setFormData({...formData, requires_prescription: e.target.checked})} 
                  />
                  Requires Prescription
                </label>
              </div>
              <div className="modal-footer">
                <button type="button" className="protera-btn protera-btn-outline" onClick={handleCloseModal}>Cancel</button>
                <button type="submit" className="protera-btn protera-btn-primary">
                  {editingItem ? 'Update Medicine' : 'Add Medicine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;