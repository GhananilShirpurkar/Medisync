export const adminState = {
  isAuthenticated: false,
  adminUser: null,
};

export const adminLogin = (username, password) => {
  if (username === 'admin' && password === 'medisync2026') {
    adminState.isAuthenticated = true;
    adminState.adminUser = username;
    return true;
  }
  return false;
};

export const adminLogout = () => {
  adminState.isAuthenticated = false;
  adminState.adminUser = null;
};

export const isAdminAuthenticated = () => adminState.isAuthenticated;
