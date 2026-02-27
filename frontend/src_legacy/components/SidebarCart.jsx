import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SidebarCart = ({ currentOrder }) => {
  const [isOpen, setIsOpen] = useState(false);

  // Example placeholder data for past orders
  const pastOrders = [
    { id: 'ORD-1234', date: 'Oct 12', items: 2, status: 'Delivered' },
    { id: 'ORD-9876', date: 'Sep 28', items: 1, status: 'Delivered' }
  ];

  const cartItemCount = currentOrder?.medications?.length || 0;

  return (
    <>
      {/* Persistent Right Edge (Zen Presence) */}
      <div 
        className={`fixed top-0 right-0 h-full w-[60px] bg-white/40 backdrop-blur-xl border-l border-white/40 z-50 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] hover:w-[80px] group ${
          isOpen ? 'translate-x-full' : 'translate-x-0'
        }`}
      >
        <button
          onClick={() => setIsOpen(true)}
          className="w-full h-full flex flex-col items-center justify-center gap-8 group"
        >
          <div className="relative">
            <span className="text-xl grayscale opacity-40 group-hover:opacity-100 group-hover:grayscale-0 transition-all duration-500">🛒</span>
            {cartItemCount > 0 && (
              <span className="absolute -top-2 -right-3 bg-[#6b8e23] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full shadow-lg shadow-[#6b8e23]/20">
                {cartItemCount}
              </span>
            )}
          </div>
          
          <div className="flex flex-col items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-slate-400 rotate-90 whitespace-nowrap origin-center">
              Inventory
            </span>
          </div>
        </button>
      </div>

      {/* Overlay: Ultra-thin blur */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/5 backdrop-blur-[2px] z-[60]"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Expanded Sliding Panel */}
      <motion.div 
        className={`fixed top-0 right-0 h-full w-full sm:w-80 md:w-96 bg-white/90 backdrop-blur-3xl shadow-[-20px_0_50px_rgba(0,0,0,0.05)] z-[70] transform transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        } flex flex-col`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-white">
          <h2 className="text-xl font-medium tracking-tight text-gray-800">Your Cart & Orders</h2>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-full hover:bg-gray-50 text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          {/* Current Cart Section */}
          <section>
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Current Order</h3>
            {currentOrder ? (
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs text-gray-500 font-medium">#{currentOrder.prescriptionId}</span>
                  <span className="text-xs bg-[#eef2e6] text-[#556b2f] px-2 py-1 rounded-full font-medium">
                    {currentOrder.interactionStatus === 'prescription_processed' ? 'Ready to Order' : 'Pending'}
                  </span>
                </div>
                <div className="space-y-3">
                  {currentOrder.medications.map((med, idx) => (
                    <div key={idx} className="flex justify-between items-start">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{med.medicine_name}</p>
                        <p className="text-xs text-gray-400">Qty: 1 • {med.dosage || ''}</p>
                      </div>
                      <p className="text-sm font-medium text-gray-800">₹{med.price}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-4 border-t border-gray-50 flex justify-between items-center">
                  <span className="text-sm text-gray-500">Total</span>
                  <span className="text-lg font-medium text-gray-900">
                    ₹{currentOrder.medications.reduce((sum, med) => sum + (med.price || 0), 0).toFixed(2)}
                  </span>
                </div>
                <button className="w-full mt-5 bg-[#6b8e23] hover:bg-[#556b2f] text-white py-3 rounded-xl text-sm font-medium transition-colors shadow-sm">
                  Checkout Now
                </button>
              </div>
            ) : (
              <div className="text-center py-8 bg-white rounded-2xl border border-gray-100 border-dashed">
                <span className="text-3xl opacity-30 block mb-2">🌿</span>
                <p className="text-sm text-gray-400">Your cart is feeling light.</p>
              </div>
            )}
          </section>

          {/* Past Orders Section */}
          <section>
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-4">Past Orders</h3>
            <div className="space-y-3">
              {pastOrders.map((order, idx) => (
                <div key={idx} className="bg-white p-4 rounded-xl border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer flex justify-between items-center group">
                  <div>
                    <p className="text-sm font-medium text-gray-800 group-hover:text-[#6b8e23] transition-colors">{order.id}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{order.date} • {order.items} items</p>
                  </div>
                  <span className="text-xs bg-gray-50 text-gray-500 px-2 py-1 rounded-md font-medium">
                    {order.status}
                  </span>
                </div>
              ))}
              <button className="w-full py-3 text-sm text-[#6b8e23] font-medium hover:bg-[#eef2e6] rounded-xl transition-colors">
                View All History
              </button>
            </div>
          </section>
        </div>
      </motion.div>
    </>
  );
};

export default SidebarCart;
