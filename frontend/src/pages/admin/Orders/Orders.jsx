import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../../../services/adminService';
import { useAdminRealtime } from '../../../hooks/useAdminRealtime';
import './Orders.css';
import { useAdminContext } from '../../../context/AdminContext';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { searchQuery } = useAdminContext();

  const filteredOrders = orders.filter(order => 
    (order.id?.toString() || '').includes(searchQuery) ||
    (order.patient?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (order.medicines?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  const fetchOrders = useCallback(async () => {
    try {
      const data = await adminService.getOrders();
      setOrders(data);
    } catch (err) {
      console.error("Failed to fetch orders:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleRealtimeEvent = useCallback((event) => {
    if (event.type === 'ORDER_CREATED' || event.type === 'ORDER_REJECTED') {
      fetchOrders();
    }
  }, [fetchOrders]);

  useAdminRealtime(handleRealtimeEvent);

  if (loading) {
    return <div className="admin-orders protera-theme">Loading...</div>;
  }

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
              {filteredOrders.map((order) => (
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