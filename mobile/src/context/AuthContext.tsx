import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ApiService } from '../services/ApiService';

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
  register: (userData: any) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (profileData: any) => Promise<void>;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStoredAuth();
  }, []);

  const loadStoredAuth = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('auth_token');
      if (storedToken) {
        setToken(storedToken);
        // Load user profile
        const userProfile = await ApiService.getUserProfile(storedToken);
        setUser(userProfile);
      }
    } catch (error) {
      console.error('Error loading stored auth:', error);
      // Clear invalid stored data
      await AsyncStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await ApiService.login(username, password);
      const { token: authToken, user_id, username: returnedUsername } = response;
      
      setToken(authToken);
      await AsyncStorage.setItem('auth_token', authToken);
      
      // Fetch full user profile
      const userProfile = await ApiService.getUserProfile(authToken);
      setUser({
        id: user_id,
        username: returnedUsername,
        ...userProfile
      });

    } catch (error: any) {
      throw new Error(error.message || 'Login failed');
    }
  };

  const register = async (userData: any): Promise<void> => {
    try {
      const response = await ApiService.register(userData);
      const { token: authToken, user_id, username } = response;
      
      setToken(authToken);
      await AsyncStorage.setItem('auth_token', authToken);
      
      // Fetch full user profile
      const userProfile = await ApiService.getUserProfile(authToken);
      setUser({
        id: user_id,
        username,
        ...userProfile
      });

    } catch (error: any) {
      throw new Error(error.message || 'Registration failed');
    }
  };

  const logout = async (): Promise<void> => {
    try {
      if (token) {
        await ApiService.logout(token);
      }
    } catch (error) {
      // Ignore logout errors
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setToken(null);
      await AsyncStorage.removeItem('auth_token');
    }
  };

  const updateProfile = async (profileData: any): Promise<void> => {
    if (!token) throw new Error('Not authenticated');

    try {
      const updatedProfile = await ApiService.updateProfile(profileData, token);
      setUser(prev => prev ? {
        ...prev,
        profile: updatedProfile
      } : null);

    } catch (error: any) {
      throw new Error(error.message || 'Profile update failed');
    }
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    updateProfile,
    isAuthenticated: !!token && !!user,
    loading
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