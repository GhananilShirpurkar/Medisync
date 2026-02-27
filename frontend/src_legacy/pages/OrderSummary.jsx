import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

const OrderSummary = () => {
  const { orderId } = useParams();
  const [orderData, setOrderData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch order details
    fetchOrderDetails();
  }, [orderId]);

  const fetchOrderDetails = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`http://localhost:8000/api/orders/${orderId}`);
      // const data = await response.json();
      
      // Mock data for now
      setOrderData({
        order_id: orderId,
        medicines: [
          { name: 'Paracetamol 500mg', quantity: 10, price: 25 },
          { name: 'Cetirizine 10mg', quantity: 10, price: 45 },
        ],
        total: 70,
        pickup_time: '30 minutes',
        telegram_sent: true,
        created_at: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Failed to fetch order:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-300 border-t-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading order details...</p>
        </div>
      </div>
    );
  }

  if (!orderData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Order Not Found</h2>
          <p className="text-gray-600 mb-6">The order you're looking for doesn't exist.</p>
          <Link
            to="/"
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
          >
            Return Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-8 px-4" aria-label="Order Summary">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Order Confirmed
          </h1>
          <p className="text-gray-600">
            Your medication is being prepared
          </p>
        </div>

        {/* Order Details Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 mb-6 border border-gray-100">
          {/* Order ID */}
          <div className="mb-6 pb-6 border-b border-gray-200">
            <p className="text-sm text-gray-600 mb-1">Order ID</p>
            <p className="text-xl font-bold text-gray-900 font-mono">
              {orderData.order_id}
            </p>
          </div>

          {/* Medicines List */}
          <div className="mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Medications</h2>
            <div className="space-y-3">
              {orderData.medicines.map((medicine, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
                >
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{medicine.name}</p>
                    <p className="text-sm text-gray-600">Quantity: {medicine.quantity}</p>
                  </div>
                  <p className="text-lg font-bold text-gray-900">
                    ₹{medicine.price}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Total */}
          <div className="mb-6 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <p className="text-xl font-bold text-gray-900">Total Amount</p>
              <p className="text-3xl font-bold text-blue-600">
                ₹{orderData.total}
              </p>
            </div>
          </div>

          {/* Pickup Time */}
          <div className="mb-6 p-4 bg-blue-50 rounded-xl border-2 border-blue-200">
            <div className="flex items-center gap-3">
              <span className="text-3xl">⏰</span>
              <div>
                <p className="text-sm text-blue-900 font-semibold">Estimated Pickup Time</p>
                <p className="text-xl font-bold text-blue-600">{orderData.pickup_time}</p>
              </div>
            </div>
          </div>

          {/* Telegram Notification Status */}
          {orderData.telegram_sent && (
            <div className="p-4 bg-green-50 rounded-xl border-2 border-green-200">
              <div className="flex items-center gap-3">
                <span className="text-3xl">✅</span>
                <div>
                  <p className="text-sm text-green-900 font-semibold">Telegram Notification Sent</p>
                  <p className="text-sm text-green-700">
                    You'll receive updates on your Telegram
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={() => window.print()}
            className="w-full px-6 py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-all duration-200 transform hover:scale-105 shadow-lg"
          >
            📄 Download Bill
          </button>
          
          <Link
            to="/"
            className="block w-full px-6 py-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition-all duration-200 text-center"
          >
            ← Return Home
          </Link>
        </div>

        {/* Additional Info */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Order placed on {new Date(orderData.created_at).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default OrderSummary;
