import React, { useState, useContext, createContext, ReactNode } from 'react';
import axios from 'axios';

interface User {
  id: number;
  username: string;
  email: string;
  profile?: {
    bio: string;
    avatar?: string;
    location: string;
    favorite_genres: string[];
    music_experience: string;
    reputation_score: number;
  };
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
  }) => Promise<void>;
  logout: () => void;
  updateProfile: (profileData: any) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = 'http://localhost:8000';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/api/login/`, {
        username,
        password
      });

      const { token: authToken, user_id, username: returnedUsername } = response.data;
      
      setToken(authToken);
      localStorage.setItem('auth_token', authToken);
      
      // Fetch full user profile
      const profileResponse = await axios.get(`${API_BASE_URL}/auth/api/profile/`, {
        headers: { Authorization: `Token ${authToken}` }
      });

      setUser({
        id: user_id,
        username: returnedUsername,
        email: profileResponse.data.email,
        profile: profileResponse.data
      });

    } catch (error: any) {
      throw new Error(error.response?.data?.non_field_errors?.[0] || 'Login failed');
    }
  };

  const register = async (userData: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name?: string;
    last_name?: string;
  }): Promise<void> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/api/register/`, userData);
      
      const { token: authToken, user_id, username } = response.data;
      
      setToken(authToken);
      localStorage.setItem('auth_token', authToken);
      
      // Fetch full user profile
      const profileResponse = await axios.get(`${API_BASE_URL}/auth/api/profile/`, {
        headers: { Authorization: `Token ${authToken}` }
      });

      setUser({
        id: user_id,
        username,
        email: userData.email,
        profile: profileResponse.data
      });

    } catch (error: any) {
      const errorMsg = error.response?.data?.username?.[0] ||
                      error.response?.data?.email?.[0] ||
                      error.response?.data?.password?.[0] ||
                      'Registration failed';
      throw new Error(errorMsg);
    }
  };

  const logout = (): void => {
    if (token) {
      // Call logout endpoint to invalidate token
      axios.post(`${API_BASE_URL}/auth/api/logout/`, {}, {
        headers: { Authorization: `Token ${token}` }
      }).catch(() => {
        // Ignore errors on logout
      });
    }
    
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  };

  const updateProfile = async (profileData: any): Promise<void> => {
    if (!token) throw new Error('Not authenticated');

    try {
      const response = await axios.put(`${API_BASE_URL}/auth/api/profile/`, profileData, {
        headers: { Authorization: `Token ${token}` }
      });

      setUser(prev => prev ? {
        ...prev,
        profile: response.data
      } : null);

    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Profile update failed');
    }
  };

  // Set up axios interceptor for auth token
  React.useEffect(() => {
    const interceptor = axios.interceptors.request.use(
      (config) => {
        if (token && config.url?.includes(API_BASE_URL)) {
          config.headers.Authorization = `Token ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    return () => axios.interceptors.request.eject(interceptor);
  }, [token]);

  // Load user on token change
  React.useEffect(() => {
    if (token && !user) {
      axios.get(`${API_BASE_URL}/auth/api/profile/`, {
        headers: { Authorization: `Token ${token}` }
      })
      .then(response => {
        setUser({
          id: response.data.id || 0,
          username: response.data.username || '',
          email: response.data.email || '',
          profile: response.data
        });
      })
      .catch(() => {
        // Token might be invalid
        logout();
      });
    }
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    updateProfile,
    isAuthenticated: !!token && !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component
export const LoginForm: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Login</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <button type="submit" disabled={loading} className="submit-btn">
        {loading ? 'Logging in...' : 'Login'}
      </button>
      
      <style jsx>{`
        .auth-form {
          max-width: 400px;
          margin: 0 auto;
          padding: 30px;
          background: #1a1a1a;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .auth-form h2 {
          color: #4a9eff;
          text-align: center;
          margin-bottom: 25px;
          font-size: 28px;
          font-weight: 600;
        }
        
        .form-group {
          margin-bottom: 20px;
        }
        
        .form-group label {
          display: block;
          color: #ccc;
          margin-bottom: 8px;
          font-weight: 500;
        }
        
        .form-group input {
          width: 100%;
          padding: 12px;
          background: #2a2a2a;
          border: 2px solid #333;
          border-radius: 8px;
          color: #fff;
          font-size: 16px;
          transition: border-color 0.3s;
        }
        
        .form-group input:focus {
          outline: none;
          border-color: #4a9eff;
        }
        
        .submit-btn {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, #4a9eff 0%, #007bff 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 15px rgba(74, 158, 255, 0.4);
        }
        
        .submit-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        
        .error-message {
          background: #ff4757;
          color: white;
          padding: 12px;
          border-radius: 6px;
          margin-bottom: 20px;
          text-align: center;
          font-weight: 500;
        }
      `}</style>
    </form>
  );
};

// Registration Component
export const RegisterForm: React.FC<{ onSuccess?: () => void }> = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (formData.password !== formData.password_confirm) {
      setError("Passwords don't match");
      setLoading(false);
      return;
    }

    try {
      await register(formData);
      onSuccess?.();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Create Account</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="first_name">First Name</label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            disabled={loading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="last_name">Last Name</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            disabled={loading}
          />
        </div>
      </div>
      
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          required
          disabled={loading}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          disabled={loading}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          required
          disabled={loading}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password_confirm">Confirm Password</label>
        <input
          type="password"
          id="password_confirm"
          name="password_confirm"
          value={formData.password_confirm}
          onChange={handleChange}
          required
          disabled={loading}
        />
      </div>
      
      <button type="submit" disabled={loading} className="submit-btn">
        {loading ? 'Creating Account...' : 'Create Account'}
      </button>
    </form>
  );
};