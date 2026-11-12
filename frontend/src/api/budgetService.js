import { API_URLS, getHeaders, handleResponse } from './http';

const API_URL = API_URLS.budget;

export async function getFamilyBudgets() {
  return handleResponse(await fetch(`${API_URL}/budgets`, {
    headers: getHeaders(false),
  }));
}

export async function saveBudget(data) {
  return handleResponse(await fetch(`${API_URL}/budgets`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  }));
}

export async function updateBudget(id, data) {
  return handleResponse(await fetch(`${API_URL}/budgets/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data),
  }));
}

export async function deleteBudget(id) {
  return handleResponse(await fetch(`${API_URL}/budgets/${id}`, {
    method: 'DELETE',
    headers: getHeaders(false),
  }));
}

export async function addExpenseOrPlan(data) {
  return handleResponse(await fetch(`${API_URL}/budgets/expenses`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(data),
  }));
}

// НОВА ФУНКЦІЯ: редагування витрати або запланованої покупки
export async function updateExpenseOrPlan(id, data) {
  return handleResponse(await fetch(`${API_URL}/budgets/expenses/${id}`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(data),
  }));
}

export async function deleteExpenseOrPlan(id) {
  return handleResponse(await fetch(`${API_URL}/budgets/expenses/${id}`, {
    method: 'DELETE',
    headers: getHeaders(false),
  }));
}
