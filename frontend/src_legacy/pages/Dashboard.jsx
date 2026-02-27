import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLowStockItems } from '../services/api';

const Dashboard = () => {
    const [stats, setStats] = useState({
        pendingOrders: 0,
        todayOrders: 0,
        lowStockItems: 0,
        totalRevenue: 0
    });
    const [pendingOrders, setPendingOrders] = useState([]);
    const [lowStockItems, setLowStockItems] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchDashboardData();

        // Auto-refresh every 30 seconds if enabled
        let interval;
        if (autoRefresh) {
            interval = setInterval(() => {
                fetchDashboardData(true); // Silent refresh
            }, 30000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [autoRefresh]);

    const fetchDashboardData = async (silent = false) => {
        if (!silent) setIsLoading(true);
        setError(null);

        try {
            // Fetch low stock items
            const stockData = await getLowStockItems();
            setLowStockItems(stockData.items || []);

            // Update stats
            setStats(prev => ({
                ...prev,
                lowStockItems: stockData.items?.length || 0,
                // TODO: Add API calls for pending orders and revenue when available
            }));
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
            if (!silent) {
                setError(err.message || 'Failed to load dashboard data. Please try again.');
            }
        } finally {
            if (!silent) setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6 flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Operator Dashboard</h1>
                        <p className="text-gray-600 mt-2">Pharmacy management console</p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setAutoRefresh(!autoRefresh)}
                            className={`px-4 py-2 rounded-lg text-sm ${autoRefresh
                                    ? 'bg-green-100 text-green-800 border border-green-300'
                                    : 'bg-gray-100 text-gray-700 border border-gray-300'
                                }`}
                        >
                            {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
                        </button>
                        <button
                            onClick={() => fetchDashboardData()}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                        >
                            Refresh Now
                        </button>
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <div className="flex items-start">
                            <div className="text-2xl mr-3">❌</div>
                            <div className="flex-1">
                                <div className="font-semibold text-red-900">Error Loading Data</div>
                                <div className="text-sm text-red-700 mt-1">{error}</div>
                                <button
                                    onClick={() => fetchDashboardData()}
                                    className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                                >
                                    Retry
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Pending Orders</div>
                        <div className="text-3xl font-bold text-gray-900">{stats.pendingOrders}</div>
                        <div className="text-xs text-gray-500 mt-1">Awaiting processing</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Today's Orders</div>
                        <div className="text-3xl font-bold text-gray-900">{stats.todayOrders}</div>
                        <div className="text-xs text-gray-500 mt-1">Last 24 hours</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Low Stock Items</div>
                        <div className="text-3xl font-bold text-orange-600">{stats.lowStockItems}</div>
                        <div className="text-xs text-gray-500 mt-1">Needs restocking</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Today's Revenue</div>
                        <div className="text-3xl font-bold text-green-600">₹{stats.totalRevenue}</div>
                        <div className="text-xs text-gray-500 mt-1">Last 24 hours</div>
                    </div>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <div className="text-4xl mb-4">⏳</div>
                        <div className="text-lg text-gray-600">Loading dashboard...</div>
                    </div>
                )}

                {/* Main Content Grid */}
                {!isLoading && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Pending Orders */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-6 border-b border-gray-200">
                                <h2 className="text-xl font-bold text-gray-900">Pending Orders</h2>
                            </div>
                            <div className="p-6">
                                {pendingOrders.length === 0 ? (
                                    <div className="text-center py-8 text-gray-500">
                                        <div className="text-4xl mb-2">✅</div>
                                        <div>No pending orders</div>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {pendingOrders.map((order) => (
                                            <div
                                                key={order.order_id}
                                                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                                                onClick={() => navigate(`/order/${order.order_id}`)}
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <div className="font-semibold text-gray-900">#{order.order_id}</div>
                                                        <div className="text-sm text-gray-600">{order.user_id}</div>
                                                    </div>
                                                    <div className="text-sm text-gray-600">
                                                        ₹{order.total_amount?.toFixed(2)}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Low Stock Alerts */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                                <h2 className="text-xl font-bold text-gray-900">Low Stock Alerts</h2>
                                <button
                                    onClick={() => navigate('/inventory')}
                                    className="text-sm text-blue-600 hover:text-blue-800"
                                >
                                    View All →
                                </button>
                            </div>
                            <div className="p-6">
                                {lowStockItems.length === 0 ? (
                                    <div className="text-center py-8 text-gray-500">
                                        <div className="text-4xl mb-2">✅</div>
                                        <div>All items well stocked</div>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {lowStockItems.slice(0, 5).map((item) => (
                                            <div
                                                key={item.id}
                                                className="p-4 border border-orange-200 bg-orange-50 rounded-lg"
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <div className="font-semibold text-gray-900">{item.name}</div>
                                                        <div className="text-sm text-gray-600">{item.category}</div>
                                                    </div>
                                                    <div className="text-right">
                                                        <div className="text-sm font-semibold text-orange-600">
                                                            {item.stock} left
                                                        </div>
                                                        <div className="text-xs text-gray-600">₹{item.price}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                        {lowStockItems.length > 5 && (
                                            <div className="text-center text-sm text-gray-600">
                                                + {lowStockItems.length - 5} more items
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                {!isLoading && (
                    <div className="mt-6 bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <button
                                onClick={() => navigate('/inventory')}
                                className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left"
                            >
                                <div className="text-2xl mb-2">📦</div>
                                <div className="font-semibold text-gray-900">Manage Inventory</div>
                                <div className="text-sm text-gray-600">View and update stock</div>
                            </button>
                            <button
                                onClick={() => navigate('/kiosk')}
                                className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left"
                            >
                                <div className="text-2xl mb-2">💬</div>
                                <div className="font-semibold text-gray-900">New Consultation</div>
                                <div className="text-sm text-gray-600">Start customer interaction</div>
                            </button>
                            <button
                                onClick={() => navigate('/prescription')}
                                className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left"
                            >
                                <div className="text-2xl mb-2">📋</div>
                                <div className="font-semibold text-gray-900">Process Prescription</div>
                                <div className="text-sm text-gray-600">Upload and validate</div>
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
