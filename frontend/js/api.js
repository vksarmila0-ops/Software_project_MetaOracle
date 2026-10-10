/**
 * MetaOracle REST API Client
 * Interfaces with FastAPI backend at /api/*
 */

const API_BASE = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? `${window.location.origin}/api`
  : '/api';

class ApiClient {
  async _request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        let errMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) {
            errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (_) {}
        throw new Error(errMessage);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err);
      throw err;
    }
  }

  // System
  async getHealth() {
    return this._request('/health');
  }

  // Dashboard Stats
  async getDashboardStats() {
    return this._request('/stats/dashboard');
  }

  // Presets
  async getPresets() {
    return this._request('/tests/presets');
  }

  // Metamorphic Testing
  async runTests(payload) {
    return this._request('/tests/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getTestHistory(category = null, status = null, limit = 50, offset = 0) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (status) params.append('status', status);
    params.append('limit', limit);
    params.append('offset', offset);
    return this._request(`/tests/history?${params.toString()}`);
  }

  async getTestRun(id) {
    return this._request(`/tests/${id}`);
  }

  async deleteTestRun(id) {
    return this._request(`/tests/${id}`, { method: 'DELETE' });
  }

  // Relations Catalog
  async getRelations() {
    return this._request('/relations');
  }

  async getRelation(id) {
    return this._request(`/relations/${id}`);
  }

  async addCustomRelation(data) {
    return this._request('/relations/custom', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async suggestRelations(payload) {
    return this._request('/relations/suggest', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Mutation Testing
  async runMutation(payload) {
    return this._request('/mutation/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getMutationHistory() {
    return this._request('/mutation/history');
  }

  async getMutationRun(id) {
    return this._request(`/mutation/${id}`);
  }

  // Benchmark Arena
  async runBenchmark(payload) {
    return this._request('/benchmark/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getBenchmarkHistory() {
    return this._request('/benchmark/history');
  }

  // Code Snippets
  async getSnippets() {
    return this._request('/snippets');
  }

  async createSnippet(data) {
    return this._request('/snippets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteSnippet(id) {
    return this._request(`/snippets/${id}`, { method: 'DELETE' });
  }
}

window.api = new ApiClient();
