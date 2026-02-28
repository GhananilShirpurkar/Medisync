const ADMIN_BASE_URL = "http://localhost:8000/api/v1/admin";

export const adminService = {
  getStats: async () => {
    const response = await fetch(`${ADMIN_BASE_URL}/stats`);
    if (!response.ok) throw new Error("Failed to fetch admin stats");
    return response.json();
  },

  getInventory: async () => {
    const response = await fetch(`${ADMIN_BASE_URL}/inventory`);
    if (!response.ok) throw new Error("Failed to fetch inventory");
    return response.json();
  },

  getCustomers: async () => {
    const response = await fetch(`${ADMIN_BASE_URL}/customers`);
    if (!response.ok) throw new Error("Failed to fetch customers");
    return response.json();
  },

  getOrders: async () => {
    const response = await fetch(`${ADMIN_BASE_URL}/orders`);
    if (!response.ok) throw new Error("Failed to fetch orders");
    return response.json();
  },

  getPendingOrders: async () => {
    const response = await fetch(`${ADMIN_BASE_URL}/pending`);
    if (!response.ok) throw new Error("Failed to fetch pending orders");
    return response.json();
  },

  handleOrderAction: async (orderId, status) => {
    const response = await fetch(`${ADMIN_BASE_URL}/orders/${orderId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error(`Failed to ${status} order`);
    return response.json();
  },

  addMedicine: async (data) => {
    const response = await fetch(`${ADMIN_BASE_URL}/inventory`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to add medicine");
    return response.json();
  },

  updateMedicine: async (id, data) => {
    const response = await fetch(`${ADMIN_BASE_URL}/inventory/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error("Failed to update medicine");
    return response.json();
  },

  deleteMedicine: async (id) => {
    const response = await fetch(`${ADMIN_BASE_URL}/inventory/${id}`, {
      method: "DELETE"
    });
    if (!response.ok) throw new Error("Failed to delete medicine");
    return response.json();
  }
};
