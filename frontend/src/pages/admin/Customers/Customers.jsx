import React from 'react';
import { useAdminContext } from '../../../context/AdminContext';

const mockCustomers = [
  { id: 'PAT-4921', phone: '+1 (555) ***-9214', registered: 'Oct 12, 2025', orders: 14, lastVisit: 'Feb 21, 2026' },
  { id: 'PAT-4922', phone: '+1 (555) ***-3382', registered: 'Nov 05, 2025', orders: 8, lastVisit: 'Feb 18, 2026' },
  { id: 'PAT-4923', phone: '+1 (555) ***-7719', registered: 'Jan 10, 2026', orders: 3, lastVisit: 'Feb 24, 2026' },
  { id: 'PAT-4924', phone: '+1 (555) ***-1150', registered: 'Aug 22, 2025', orders: 21, lastVisit: 'Feb 15, 2026' },
  { id: 'PAT-4925', phone: '+1 (555) ***-8492', registered: 'Dec 02, 2025', orders: 5, lastVisit: 'Feb 20, 2026' },
  { id: 'PAT-4926', phone: '+1 (555) ***-2039', registered: 'Jan 28, 2026', orders: 2, lastVisit: 'Feb 23, 2026' },
  { id: 'PAT-4927', phone: '+1 (555) ***-5561', registered: 'Sep 15, 2025', orders: 11, lastVisit: 'Feb 19, 2026' },
  { id: 'PAT-4928', phone: '+1 (555) ***-4827', registered: 'Nov 18, 2025', orders: 7, lastVisit: 'Feb 22, 2026' },
  { id: 'PAT-4929', phone: '+1 (555) ***-9934', registered: 'Oct 30, 2025', orders: 9, lastVisit: 'Feb 14, 2026' },
  { id: 'PAT-4930', phone: '+1 (555) ***-6210', registered: 'Feb 05, 2026', orders: 1, lastVisit: 'Feb 05, 2026' },
  { id: 'PAT-4931', phone: '+1 (555) ***-1748', registered: 'Jul 08, 2025', orders: 28, lastVisit: 'Feb 24, 2026' },
  { id: 'PAT-4932', phone: '+1 (555) ***-3095', registered: 'Dec 15, 2025', orders: 4, lastVisit: 'Jan 30, 2026' },
  { id: 'PAT-4933', phone: '+1 (555) ***-8821', registered: 'Sep 02, 2025', orders: 16, lastVisit: 'Feb 12, 2026' },
  { id: 'PAT-4934', phone: '+1 (555) ***-4506', registered: 'Jan 19, 2026', orders: 3, lastVisit: 'Feb 21, 2026' },
  { id: 'PAT-4935', phone: '+1 (555) ***-7133', registered: 'Oct 25, 2025', orders: 10, lastVisit: 'Feb 17, 2026' }
];

const Customers = () => {
  const { searchQuery } = useAdminContext();

  const filteredCustomers = mockCustomers.filter(customer =>
    (customer.id?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (customer.phone?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  return (
    <div className="admin-customers protera-theme">
      <div className="protera-main-column">
        <div className="protera-table-card">
          <h3 className="card-title">Patient Records</h3>

          <table className="protera-table">
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
              {filteredCustomers.map((customer) => (
                <tr key={customer.id}>
                  <td className="font-medium text-dark">{customer.id}</td>
                  <td style={{ color: '#6b7280' }}>{customer.phone}</td>
                  <td>{customer.registered}</td>
                  <td>{customer.orders}</td>
                  <td>{customer.lastVisit}</td>
                </tr>
              ))}
              {filteredCustomers.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
                    No patients found matching your search.
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

export default Customers;