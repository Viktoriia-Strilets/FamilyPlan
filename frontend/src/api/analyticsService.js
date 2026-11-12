import { API_URLS, getHeaders, handleResponse } from './http';
const API_URL = API_URLS.analytics;

export async function getReports() {
  return handleResponse(await fetch(`${API_URL}/reports/`, { headers: getHeaders(false) }));
}

export async function createReport(data) {
  return handleResponse(await fetch(`${API_URL}/reports/`, {
    method: 'POST', headers: getHeaders(), body: JSON.stringify(data),
  }));
}

export async function deleteReport(id) {
  return handleResponse(await fetch(`${API_URL}/reports/${id}`, {
    method: 'DELETE', headers: getHeaders(false),
  }));
}

export async function getForecast() {
  return handleResponse(await fetch(`${API_URL}/analytics/forecast`, {
    headers: getHeaders(false),
  }));
}

export async function getCategoryStatistics(period) {
  return handleResponse(await fetch(`${API_URL}/analytics/categories/${period}`, {
    headers: getHeaders(false),
  }));
}