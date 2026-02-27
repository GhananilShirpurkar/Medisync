import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import Landing from './pages/Landing';
import Kiosk from './pages/Kiosk';
import OrderSummary from './pages/OrderSummary';
import Prescription from './pages/Prescription';
import OrderHistory from './pages/OrderHistory';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-transparent text-slate-100">
        <Routes>
          {/* Customer Routes */}
          <Route path="/" element={<Kiosk />} />
          <Route path="/prescription" element={<Prescription />} />
          <Route path="/order/:orderId" element={<OrderSummary />} />
          <Route path="/orders" element={<OrderHistory />} />

          {/* Operator Routes */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/inventory" element={<Inventory />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
