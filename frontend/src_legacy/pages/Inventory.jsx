import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchMedicines } from '../services/api';

const Inventory = () => {
    const [medicines, setMedicines] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedMedicine, setSelectedMedicine] = useState(null);
    const [filterCategory, setFilterCategory] = useState('all');
    const [filterRx, setFilterRx] = useState('all');
    const navigate = useNavigate();

    // Debounced search
    useEffect(() => {
        if (searchQuery.length >= 2) {
            const timer = setTimeout(() => {
                performSearch();
            }, 500); // 500ms debounce

            return () => clearTimeout(timer);
        } else {
            setMedicines([]);
        }
    }, [searchQuery]);

    const performSearch = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await searchMedicines(searchQuery);
            setMedicines(data.results || []);
        } catch (err) {
            console.error('Search failed:', err);
            setError(err.message || 'Failed to search medicines. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const getStockStatus = (stock) => {
        if (stock === 0) return { label: 'Out of Stock', color: 'text-red-600', bgColor: 'bg-red-50' };
        if (stock < 10) return { label: 'Low Stock', color: 'text-orange-600', bgColor: 'bg-orange-50' };
        return { label: 'In Stock', color: 'text-green-600', bgColor: 'bg-green-50' };
    };

    // Get unique categories
    const categories = [...new Set(medicines.map(m => m.category))];

    // Filter medicines
    const filteredMedicines = medicines.filter(med => {
        const categoryMatch = filterCategory === 'all' || med.category === filterCategory;
        const rxMatch = filterRx === 'all' ||
            (filterRx === 'rx' && med.requires_prescription) ||
            (filterRx === 'otc' && !med.requires_prescription);
        return categoryMatch && rxMatch;
    });

    return (
        <div className="min-h-screen bg-gray-50 p-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="text-blue-600 hover:text-blue-800 mb-4"
                    >
                        ← Back to Dashboard
                    </button>
                    <h1 className="text-3xl font-bold text-gray-900">Inventory Management</h1>
                    <p className="text-gray-600 mt-2">Search and manage medicine stock</p>
                </div>

                {/* Search Bar */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <div className="relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search medicines by name..."
                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        {isLoading && (
                            <div className="absolute right-3 top-3 text-gray-400">
                                <div className="animate-spin">⏳</div>
                            </div>
                        )}
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                        Type at least 2 characters to search • {medicines.length} results found
                    </p>
                </div>

                {/* Filters */}
                {medicines.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-4 mb-6">
                        <div className="flex flex-wrap gap-4">
                            {/* Category Filter */}
                            <div>
                                <label className="text-sm font-semibold text-gray-700 mb-2 block">Category</label>
                                <select
                                    value={filterCategory}
                                    onChange={(e) => setFilterCategory(e.target.value)}
                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="all">All Categories</option>
                                    {categories.map(cat => (
                                        <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                </select>
                            </div>

                            {/* Prescription Filter */}
                            <div>
                                <label className="text-sm font-semibold text-gray-700 mb-2 block">Prescription</label>
                                <select
                                    value={filterRx}
                                    onChange={(e) => setFilterRx(e.target.value)}
                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="all">All Types</option>
                                    <option value="rx">Rx Required</option>
                                    <option value="otc">OTC Only</option>
                                </select>
                            </div>

                            {/* Results Count */}
                            <div className="ml-auto flex items-end">
                                <div className="text-sm text-gray-600">
                                    Showing {filteredMedicines.length} of {medicines.length} medicines
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <div className="flex items-start">
                            <div className="text-2xl mr-3">❌</div>
                            <div className="flex-1">
                                <div className="font-semibold text-red-900">Search Failed</div>
                                <div className="text-sm text-red-700 mt-1">{error}</div>
                                <button
                                    onClick={performSearch}
                                    className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                                >
                                    Retry
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!isLoading && searchQuery.length >= 2 && filteredMedicines.length === 0 && (
                    <div className="bg-white rounded-lg shadow p-8 text-center">
                        <div className="text-6xl mb-4">🔍</div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">No medicines found</h2>
                        <p className="text-gray-600">
                            {medicines.length > 0
                                ? 'Try adjusting your filters'
                                : 'Try a different search term'
                            }
                        </p>
                    </div>
                )}

                {/* Results Table */}
                {!isLoading && filteredMedicines.length > 0 && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Category</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Price</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Stock</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                                        <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Rx</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {filteredMedicines.map((medicine) => {
                                        const stockStatus = getStockStatus(medicine.stock);
                                        return (
                                            <tr
                                                key={medicine.id}
                                                className="hover:bg-gray-50 cursor-pointer"
                                                onClick={() => setSelectedMedicine(medicine)}
                                            >
                                                <td className="px-6 py-4">
                                                    <div className="font-semibold text-gray-900">{medicine.name}</div>
                                                    <div className="text-sm text-gray-600">{medicine.manufacturer}</div>
                                                </td>
                                                <td className="px-6 py-4 text-sm text-gray-700">{medicine.category}</td>
                                                <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                                                    ₹{medicine.price?.toFixed(2)}
                                                </td>
                                                <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                                                    {medicine.stock}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`text-sm font-semibold ${stockStatus.color}`}>
                                                        {stockStatus.label}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-sm">
                                                    {medicine.requires_prescription ? (
                                                        <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">
                                                            Required
                                                        </span>
                                                    ) : (
                                                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                                                            OTC
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Medicine Details Modal */}
                {selectedMedicine && (
                    <div
                        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
                        onClick={() => setSelectedMedicine(null)}
                    >
                        <div
                            className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <h2 className="text-2xl font-bold text-gray-900">{selectedMedicine.name}</h2>
                                <button
                                    onClick={() => setSelectedMedicine(null)}
                                    className="text-gray-500 hover:text-gray-700 text-2xl"
                                >
                                    ×
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <div className="text-sm text-gray-600">Manufacturer</div>
                                    <div className="font-semibold text-gray-900">{selectedMedicine.manufacturer}</div>
                                </div>

                                <div>
                                    <div className="text-sm text-gray-600">Category</div>
                                    <div className="font-semibold text-gray-900">{selectedMedicine.category}</div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-gray-600">Price</div>
                                        <div className="text-xl font-bold text-gray-900">
                                            ₹{selectedMedicine.price?.toFixed(2)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-gray-600">Stock</div>
                                        <div className={`text-xl font-bold ${getStockStatus(selectedMedicine.stock).color}`}>
                                            {selectedMedicine.stock}
                                        </div>
                                    </div>
                                </div>

                                {selectedMedicine.description && (
                                    <div>
                                        <div className="text-sm text-gray-600">Description</div>
                                        <div className="text-gray-900">{selectedMedicine.description}</div>
                                    </div>
                                )}

                                <div>
                                    <div className="text-sm text-gray-600">Prescription Required</div>
                                    <div className="font-semibold text-gray-900">
                                        {selectedMedicine.requires_prescription ? 'Yes' : 'No (OTC)'}
                                    </div>
                                </div>

                                {/* Stock Status Badge */}
                                <div className={`p-4 rounded-lg ${getStockStatus(selectedMedicine.stock).bgColor}`}>
                                    <div className={`font-semibold ${getStockStatus(selectedMedicine.stock).color}`}>
                                        {getStockStatus(selectedMedicine.stock).label}
                                    </div>
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={() => setSelectedMedicine(null)}
                                    className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Inventory;
