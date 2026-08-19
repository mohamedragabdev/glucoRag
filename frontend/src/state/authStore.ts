import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface User {
  id: number;
  name: string;
  email: string;
  created_at?: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('mrag_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('mrag_token');
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/login', { email, password });
      const { user: userData, token: tokenData } = response.data;
      localStorage.setItem('mrag_user', JSON.stringify(userData));
      localStorage.setItem('mrag_token', tokenData);
      setUser(userData);
      setToken(tokenData);
      return { success: true };
    } catch (err: any) {
      const message = err.response?.data?.message || err.response?.data?.errors?.email?.[0] || 'Login failed. Please check your credentials.';
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string, password_confirmation: string) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/register', {
        name,
        email,
        password,
        password_confirmation,
      });
      const { user: userData, token: tokenData } = response.data;
      localStorage.setItem('mrag_user', JSON.stringify(userData));
      localStorage.setItem('mrag_token', tokenData);
      setUser(userData);
      setToken(tokenData);
      return { success: true };
    } catch (err: any) {
      const errorsObj = err.response?.data?.errors || {};
      const firstErrorArray = Object.values(errorsObj)[0] as string[] | undefined;
      const message = err.response?.data?.message || firstErrorArray?.[0] || 'Registration failed.';
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.post('/logout');
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('mrag_user');
      localStorage.removeItem('mrag_token');
      setUser(null);
      setToken(null);
    }
  };

  return {
    user,
    token,
    isAuthenticated: !!token,
    loading,
    login,
    register,
    logout,
  };
}
