import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="text-6xl mb-4">💊</div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">MediSync</h1>
          <p className="text-lg text-gray-600">AI-Powered Pharmacy Assistant</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          <Link
            to="/kiosk"
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition text-center"
          >
            <div className="text-4xl mb-3">💬</div>
            <h3 className="font-bold text-gray-900 mb-2">Describe Symptoms</h3>
            <p className="text-sm text-gray-600">Get medicine recommendations</p>
          </Link>

          <Link
            to="/prescription"
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition text-center"
          >
            <div className="text-4xl mb-3">📋</div>
            <h3 className="font-bold text-gray-900 mb-2">Upload Prescription</h3>
            <p className="text-sm text-gray-600">Validate and process</p>
          </Link>

          <Link
            to="/kiosk"
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition text-center"
          >
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="font-bold text-gray-900 mb-2">Search Medicine</h3>
            <p className="text-sm text-gray-600">Find specific medicines</p>
          </Link>

          <Link
            to="/orders"
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition text-center"
          >
            <div className="text-4xl mb-3">📦</div>
            <h3 className="font-bold text-gray-900 mb-2">My Orders</h3>
            <p className="text-sm text-gray-600">View order history</p>
          </Link>
        </div>

        {/* Features */}
        <div className="bg-white rounded-lg shadow p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Key Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl mb-3">🤖</div>
              <h3 className="font-bold text-gray-900 mb-2">AI-Powered</h3>
              <p className="text-sm text-gray-600">Multi-agent system for accurate recommendations</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">⚕️</div>
              <h3 className="font-bold text-gray-900 mb-2">Safety First</h3>
              <p className="text-sm text-gray-600">Drug interaction and safety checks</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">🎤</div>
              <h3 className="font-bold text-gray-900 mb-2">Voice Support</h3>
              <p className="text-sm text-gray-600">Speak your symptoms naturally</p>
            </div>
          </div>
        </div>

        {/* Operator Access */}
        <div className="text-center">
          <p className="text-sm text-gray-600 mb-3">Pharmacy Operator?</p>
          <Link
            to="/dashboard"
            className="inline-block px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition"
          >
            Access Operator Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Landing;
