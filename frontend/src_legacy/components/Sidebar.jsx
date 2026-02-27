const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', active: false },
    { name: 'Orders', active: true },
    { name: 'Inventory', active: false },
    { name: 'Audit Logs', active: false },
    { name: 'Agents', active: false },
  ];

  return (
    <div className="w-60 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">MediSync</h1>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.name}>
              <button
                className={`w-full text-left px-4 py-2 rounded ${
                  item.active
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                {item.name}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;
