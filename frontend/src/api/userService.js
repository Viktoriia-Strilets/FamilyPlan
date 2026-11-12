import { API_URLS, getHeaders, handleResponse } from './http';
const API_URL = API_URLS.users;

export async function getCurrentUser() {
  return handleResponse(await fetch(`${API_URL}/users/me`, { headers: getHeaders(false) }));
}

export async function getUsers() {
  return handleResponse(await fetch(`${API_URL}/users`, { headers: getHeaders(false) }));
}

export async function createUser(userData) {
  return handleResponse(await fetch(`${API_URL}/users/register`, {
    method: 'POST', headers: getHeaders(), body: JSON.stringify(userData),
  }));
}

export async function updateUser(userId, userData) {
  return handleResponse(await fetch(`${API_URL}/users/${userId}`, {
    method: 'PUT', headers: getHeaders(), body: JSON.stringify(userData),
  }));
}

export async function deleteUser(userId) {
  return handleResponse(await fetch(`${API_URL}/users/${userId}`, {
    method: 'DELETE', headers: getHeaders(false),
  }));
}

export async function getAdminFamilies() {
  return handleResponse(await fetch(`${API_URL}/admin/families`, {
    headers: getHeaders(false),
  }));
}

export async function deleteAdminFamily(familyId) {
  return handleResponse(await fetch(`${API_URL}/admin/families/${familyId}`, {
    method: 'DELETE', headers: getHeaders(false),
  }));
}

export async function changePassword(passwordData) {
  return handleResponse(await fetch(`${API_URL}/users/me/password`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(passwordData),
  }));
}