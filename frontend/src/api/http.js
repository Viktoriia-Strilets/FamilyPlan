export const API_URLS = {
  users: import.meta.env.VITE_USERS_API_URL || 'http://localhost:8001',
  budget: import.meta.env.VITE_BUDGET_API_URL || 'http://localhost:8002',
  shopping: import.meta.env.VITE_SHOPPING_API_URL || 'http://localhost:8003',
  analytics: import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:8004',
};

export const getHeaders = (includeContentType = true) => {
  const token = sessionStorage.getItem('token');
  return {
    ...(includeContentType ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export async function handleResponse(response) {
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || data.message;
    throw new Error(
      typeof detail === 'string' ? detail : `Помилка запиту (${response.status})`
    );
  }
  return data;
}

export async function request(url, options = {}) {
  const response = await fetch(url, options);
  return handleResponse(response);
}