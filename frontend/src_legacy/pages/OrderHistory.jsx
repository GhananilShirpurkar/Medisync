import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserOrders } from '../services/api';

const OrderHistory = () => {
    const [orders, setOrders] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [userId, setUserId] = useState('user123'); // Default user for demo
    const [filterStatus, setFilterStatus] = useState('all');
    const navigate = useNavigate();

    useEffect(() => {
        fetchOrders();
    }, [userId]);

    const fetchOrders = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getUserOrders(userId);
            setOrders(data.orders || []);
        } catch (err) {
            console.error('Failed to fetch orders:', err);
            setError(err.message || 'Failed to load orders. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'fulfilled':
                return 'bg-green-100 text-green-800';
            case 'pending':
                return 'bg-yellow-100 text-yellow-800';
            case 'rejected':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const filteredOrders = filterStatus === 'all'
        ? orders
        : orders.filter(order => order.status === filterStatus);

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/')}
                        className="text-blue-600 hover:text-blue-800 mb-4"
                    >
                        ← Back to Home
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Order History</h1>
                    <p className="text-gray-600 mt-2">View your past orders</p>
                </div>

                {/* Filter Buttons */}
                {!isLoading && orders.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-4 mb-6">
                        <div className="flex gap-2 flex-wrap">
                            <button
                                onClick={() => setFilterStatus('all')}
                                className={`px-4 py-2 rounded-lg transition ${filterStatus === 'all'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                All ({orders.length})
                            </button>
                            <button
                                onClick={() => setFilterStatus('pending')}
                                className={`px-4 py-2 rounded-lg transition ${filterStatus === 'pending'
                                        ? 'bg-yellow-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Pending ({orders.filter(o => o.status === 'pending').length})
                            </button>
                            <button
                                onClick={() => setFilterStatus('fulfilled')}
                                className={`px-4 py-2 rounded-lg transition ${filterStatus === 'fulfilled'
                                        ? 'bg-green-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Fulfilled ({orders.filter(o => o.status === 'fulfilled').length})
                            </button>
                            <button
                                onClick={() => setFilterStatus('rejected')}
                                className={`px-4 py-2 rounded-lg transition ${filterStatus === 'rejected'
                                        ? 'bg-red-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                Rejected ({orders.filter(o => o.status === 'rejected').length})
                            </button>
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
                        <div className="flex items-start">
                            <div className="text-2xl mr-3">❌</div>
                            <div className="flex-1">
                                <div className="font-semibold text-red-900">Error Loading Orders</div>
                                <div className="text-sm text-red-700 mt-1">{error}</div>
                                <button
                                    onClick={fetchOrders}
                                    className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                                >
                                    Retry
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <div className="text-4xl mb-4">⏳</div>
                        <div className="text-lg text-gray-600">Loading orders...</div>
                    </div>
                )}

                {/* Empty State */}
                {!isLoading && !error && filteredOrders.length === 0 && (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <div className="text-6xl mb-4">📦</div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            {filterStatus === 'all' ? 'No orders yet' : `No ${filterStatus} orders`}
                        </h2>
                        <p className="text-gray-600 mb-6">
                            {filterStatus === 'all'
                                ? 'Start by describing your symptoms or uploading a prescription'
                                : `You don't have any ${filterStatus} orders`
                            }
                        </p>
                        {filterStatus === 'all' && (
                            <button
                                onClick={() => navigate('/kiosk')}
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                Start Consultation
                            </button>
                        )}
                    </div>
                )}

                {/* Orders List */}
                {!isLoading && !error && filteredOrders.length > 0 && (
                    <div className="space-y-4">
                        {filteredOrders.map((order) => (
                            <div
                                key={order.order_id}
                                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition cursor-pointer"
                                onClick={() => navigate(`/order/${order.order_id}`)}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-lg font-bold text-gray-900">
                                            Order #{order.order_id}
                                        </h3>
                                        <p className="text-sm text-gray-600">
                                            {new Date(order.created_at).toLocaleDateString('en-IN', {
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(order.status)}`}>
                                        {order.status}
                                    </span>
                                </div>

                                {/* Order Items */}
                                <div className="mb-4">
                                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Items:</h4>
                                    <ul className="space-y-1">
                                        {order.items && order.items.slice(0, 3).map((item, idx) => (
                                            <li key={idx} className="text-sm text-gray-600">
                                                • {item.medicine_name} {item.dosage && `(${item.dosage})`} - Qty: {item.quantity}
                                            </li>
                                        ))}
                                        {order.items && order.items.length > 3 && (
                                            <li className="text-sm text-gray-500">
                                                + {order.items.length - 3} more items
                                            </li>
                                        )}
                                    </ul>
                                </div>

                                {/* Total Amount */}
                                <div className="flex justify-between items-center pt-4 border-t border-gray-200">
                                    <span className="text-sm text-gray-600">Total Amount</span>
                                    <span className="text-lg font-bold text-gray-900">
                                        ₹{order.total_amount?.toFixed(2) || '0.00'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Refresh Button */}
                {!isLoading && !error && orders.length > 0 && (
                    <div className="mt-6 text-center">
                        <button
                            onClick={fetchOrders}
                            className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                        >
                            Refresh Orders
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default OrderHistory;
