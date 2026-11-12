import { API_URLS, getHeaders, handleResponse } from './http';
const API_URL = API_URLS.shopping;

export async function getShoppingItems() {
  return handleResponse(await fetch(`${API_URL}/items`, { headers: getHeaders(false) }));
}

export async function createShoppingItem(data) {
  return handleResponse(await fetch(`${API_URL}/items`, {
    method: 'POST', headers: getHeaders(), body: JSON.stringify(data),
  }));
}

export async function updateShoppingItem(id, data) {
  return handleResponse(await fetch(`${API_URL}/items/${id}`, {
    method: 'PUT', headers: getHeaders(), body: JSON.stringify(data),
  }));
}

export async function markItemAsPurchased(id, actualPrice) {
  const price = Number(actualPrice);

  if (
    actualPrice === '' ||
    actualPrice == null ||
    !Number.isFinite(price) ||
    price <= 0
  ) {
    throw new Error(
      'Вкажіть фактичну ціну покупки, більшу за нуль.'
    );
  }

  return handleResponse(
    await fetch(`${API_URL}/items/${id}/buy`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify({
        actual_price: price,
      }),
    })
  );
}

export async function deleteShoppingItem(id) {
  return handleResponse(await fetch(`${API_URL}/items/${id}`, {
    method: 'DELETE', headers: getHeaders(false),
  }));
}

export async function getPurchaseHistory() {
  return handleResponse(await fetch(`${API_URL}/history`, { headers: getHeaders(false) }));
}

export async function getShoppingRecommendations() {
  return handleResponse(await fetch(`${API_URL}/recommendations`, { headers: getHeaders(false) }));
}

export async function getShoppingReminders() {
  return handleResponse(await fetch(`${API_URL}/reminders`, { headers: getHeaders(false) }));
}