import React from 'react';
import './Inventory.css';

const mockInventory = [
  { id: 1, name: 'Paracetamol 500mg', category: 'Analgesic', stock: 145, price: '$0.05', status: 'ACTIVE' },
  { id: 2, name: 'Ibuprofen 400mg', category: 'NSAID', stock: 89, price: '$0.12', status: 'ACTIVE' },
  { id: 3, name: 'Amoxicillin 500mg', category: 'Antibiotic', stock: 8, price: '$0.45', status: 'ACTIVE' },
  { id: 4, name: 'Lisinopril 10mg', category: 'Antihypertensive', stock: 24, price: '$0.18', status: 'ACTIVE' },
  { id: 5, name: 'Metformin 850mg', category: 'Antidiabetic', stock: 210, price: '$0.08', status: 'ACTIVE' },
  { id: 6, name: 'Atorvastatin 20mg', category: 'Statin', stock: 56, price: '$0.30', status: 'ACTIVE' },
  { id: 7, name: 'Levothyroxine 50mcg', category: 'Thyroid Hormone', stock: 15, price: '$0.22', status: 'ACTIVE' },
  { id: 8, name: 'Omeprazole 20mg', category: 'PPI', stock: 112, price: '$0.25', status: 'ACTIVE' },
  { id: 9, name: 'Amlodipine 5mg', category: 'Antihypertensive', stock: 94, price: '$0.15', status: 'ACTIVE' },
  { id: 10, name: 'Azithromycin 250mg', category: 'Antibiotic', stock: 4, price: '$1.20', status: 'ACTIVE' },
  { id: 11, name: 'Losartan 50mg', category: 'Antihypertensive', stock: 43, price: '$0.28', status: 'ACTIVE' },
  { id: 12, name: 'Albuterol Inhaler', category: 'Bronchodilator', stock: 32, price: '$24.50', status: 'ACTIVE' },
  { id: 13, name: 'Gabapentin 300mg', category: 'Anticonvulsant', stock: 78, price: '$0.35', status: 'ACTIVE' },
  { id: 14, name: 'Hydrochlorothiazide 25mg', category: 'Diuretic', stock: 120, price: '$0.10', status: 'ACTIVE' },
  { id: 15, name: 'Sertraline 50mg', category: 'Antidepressant', stock: 65, price: '$0.40', status: 'ACTIVE' },
  { id: 16, name: 'Montelukast 10mg', category: 'Leukotriene Receptor Antagonist', stock: 48, price: '$0.55', status: 'ACTIVE' },
  { id: 17, name: 'Fluticasone Nasal Spray', category: 'Corticosteroid', stock: 12, price: '$18.00', status: 'ACTIVE' },
  { id: 18, name: 'Citalopram 20mg', category: 'SSRIs', stock: 0, price: '$0.32', status: 'OUT OF STOCK' },
  { id: 19, name: 'Pravastatin 40mg', category: 'Statin', stock: 27, price: '$0.28', status: 'ACTIVE' },
  { id: 20, name: 'Lorazepam 1mg', category: 'Benzodiazepine', stock: 18, price: '$0.45', status: 'ACTIVE' }
];

const Inventory = () => {
  const filteredInventory = mockInventory;

  const renderStock = (stock) => {
    if (stock < 10) {
      return <span className="stock-critical">{stock} <span className="stock-label">LOW</span></span>;
    } else if (stock <= 30) {
      return <span className="stock-warn">{stock}</span>;
    }
    return <span className="stock-good">{stock}</span>;
  };

  return (
    <div className="admin-inventory protera-theme">
      <div className="protera-main-column">
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Inventory;