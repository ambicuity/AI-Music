import axios, { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Change for production

interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success?: boolean;
}

class ApiServiceClass {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.api.interceptors.request.use(
      (config) => {
        // Token will be added dynamically where needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          console.error('Unauthorized access - token may be expired');
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  async login(username: string, password: string): Promise<any> {
    try {
      const response = await this.api.post('/auth/api/login/', {
        username,
        password,
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
  }): Promise<any> {
    try {
      const response = await this.api.post('/auth/api/register/', userData);
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async logout(token: string): Promise<void> {
    try {
      await this.api.post('/auth/api/logout/', {}, {
        headers: { Authorization: `Token ${token}` }
      });
    } catch (error: any) {
      // Ignore logout errors
      console.error('Logout error:', error);
    }
  }

  async getUserProfile(token: string): Promise<any> {
    try {
      const response = await this.api.get('/auth/api/profile/', {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async updateProfile(profileData: any, token: string): Promise<any> {
    try {
      const response = await this.api.put('/auth/api/profile/', profileData, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // AI Model endpoints
  async getAIModels(): Promise<any[]> {
    try {
      const response = await this.api.get('/ai/api/models/');
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getModelRecommendations(parameters: any, token: string): Promise<any[]> {
    try {
      const response = await this.api.post('/ai/api/models/recommend/', parameters, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async generateComposition(parameters: any, token: string): Promise<any> {
    try {
      const response = await this.api.post('/ai/api/generate/', parameters, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getGenerationRequests(token: string): Promise<any[]> {
    try {
      const response = await this.api.get('/ai/api/requests/', {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getGenerationStatus(requestId: number, token: string): Promise<any> {
    try {
      const response = await this.api.get(`/ai/api/requests/${requestId}/status/`, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Composition endpoints
  async getCompositions(token?: string): Promise<any[]> {
    try {
      const headers = token ? { Authorization: `Token ${token}` } : {};
      const response = await this.api.get('/composition/api/compositions/', { headers });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getGenres(): Promise<any[]> {
    try {
      const response = await this.api.get('/composition/api/genres/');
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async likeComposition(compositionId: number, token: string): Promise<any> {
    try {
      const response = await this.api.post(`/composition/api/compositions/${compositionId}/like/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Streaming endpoints
  async getTracks(params?: any): Promise<any[]> {
    try {
      const response = await this.api.get('/streaming/api/tracks/', { params });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getRecommendations(token: string): Promise<any[]> {
    try {
      const response = await this.api.get('/streaming/api/tracks/recommendations/', {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getTrendingTracks(): Promise<any[]> {
    try {
      const response = await this.api.get('/streaming/api/tracks/trending/');
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async searchTracks(query: string, token?: string): Promise<any[]> {
    try {
      const headers = token ? { Authorization: `Token ${token}` } : {};
      const response = await this.api.get('/streaming/api/tracks/', {
        params: { search: query },
        headers
      });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async playTrack(trackId: number, token?: string): Promise<any> {
    try {
      const headers = token ? { Authorization: `Token ${token}` } : {};
      const response = await this.api.post(`/streaming/api/tracks/${trackId}/play/`, {}, { headers });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Social features
  async getUserFeed(token: string): Promise<any[]> {
    try {
      const response = await this.api.get('/auth/api/feed/', {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async followUser(username: string, token: string): Promise<any> {
    try {
      const response = await this.api.post(`/auth/api/follow/${username}/`, {}, {
        headers: { Authorization: `Token ${token}` }
      });
      return response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  async getUsers(token?: string): Promise<any[]> {
    try {
      const headers = token ? { Authorization: `Token ${token}` } : {};
      const response = await this.api.get('/auth/api/users/', { headers });
      return response.data.results || response.data;
    } catch (error: any) {
      throw this.handleError(error);
    }
  }

  // Error handling
  private handleError(error: any): Error {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || 
                     error.response.data?.message ||
                     error.response.data?.error ||
                     'An error occurred';
      return new Error(message);
    } else if (error.request) {
      // Network error
      return new Error('Network error - please check your connection');
    } else {
      // Other error
      return new Error(error.message || 'An unexpected error occurred');
    }
  }

  // Utility methods
  setAuthToken(token: string) {
    this.api.defaults.headers.common['Authorization'] = `Token ${token}`;
  }

  removeAuthToken() {
    delete this.api.defaults.headers.common['Authorization'];
  }
}

export const ApiService = new ApiServiceClass();