import { API_URLS, handleResponse } from './http';

const API_URL = API_URLS.users;

export async function loginUser(credentials) {
  return handleResponse(await fetch(`${API_URL}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  }));
}

export async function registerUser(userData) {
  return handleResponse(await fetch(`${API_URL}/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  }));
}

export function getGoogleLoginUrl() {
  return `${API_URL}/auth/google/login`;
}

export async function completeGoogleRegistration(data) {
  return handleResponse(await fetch(`${API_URL}/auth/google/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }));
}

export async function createGoogleLinkToken(token) {
  return handleResponse(await fetch(`${API_URL}/auth/google/link-token`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }));
}

export function getGoogleLinkUrl(linkToken) {
  const url = new URL(`${API_URL}/auth/google/link`);
  url.searchParams.set('link_token', linkToken);
  return url.toString();
}