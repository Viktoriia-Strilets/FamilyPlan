import { API_URLS, getHeaders, handleResponse } from './http';
const API_URL = API_URLS.users;

export async function getFamilies() {
  return handleResponse(await fetch(`${API_URL}/families`, { headers: getHeaders(false) }));
}

export async function createFamily(familyData) {
  return handleResponse(await fetch(`${API_URL}/families`, {
    method: 'POST', headers: getHeaders(), body: JSON.stringify(familyData),
  }));
}

export async function updateFamily(familyId, familyData) {
  return handleResponse(await fetch(`${API_URL}/families/${familyId}`, {
    method: 'PUT', headers: getHeaders(), body: JSON.stringify(familyData),
  }));
}

export async function getFamilyMembers(familyId) {
  return handleResponse(await fetch(`${API_URL}/families/${familyId}/members`, {
    headers: getHeaders(false),
  }));
}

export async function deleteFamily(familyId) {
  return handleResponse(await fetch(`${API_URL}/families/${familyId}`, {
    method: 'DELETE',
    headers: getHeaders(false),
  }));
}