import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('meticul_token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('meticul_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [theme, setThemeState] = useState(() => localStorage.getItem('meticul_theme') || 'light');
  const [loading, setLoading] = useState(true);

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('meticul_theme', theme);
  }, [theme]);

  const setTheme = (newTheme) => {
    setThemeState(newTheme);
  };

  // Verify token on initial load
  useEffect(() => {
    const verifyUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
          if (data.theme) {
            setThemeState(data.theme);
          }
        } else {
          // Token expired or invalid
          logout();
        }
      } catch (err) {
        console.error('Failed to verify token:', err);
      } finally {
        setLoading(false);
      }
    };

    verifyUser();
  }, [token]);

  const login = async (username, password) => {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Login failed');
    }
    localStorage.setItem('meticul_token', data.token);
    localStorage.setItem('meticul_user', JSON.stringify(data.user));
    setToken(data.token);
    setUser(data.user);
    if (data.user.theme) {
      setThemeState(data.user.theme);
    }
    return data;
  };

  const signup = async (username, password, confirmPassword) => {
    const res = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        confirm_password: confirmPassword
      })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Signup failed');
    }
    localStorage.setItem('meticul_token', data.token);
    localStorage.setItem('meticul_user', JSON.stringify(data.user));
    setToken(data.token);
    setUser(data.user);
    if (data.user.theme) {
      setThemeState(data.user.theme);
    }
    return data;
  };

  const logout = () => {
    localStorage.removeItem('meticul_token');
    localStorage.removeItem('meticul_user');
    setToken(null);
    setUser(null);
  };

  // Helper fetch method with automatic authorization header
  const apiFetch = async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...(options.headers || {})
    };

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers
    });

    if (res.status === 401) {
      logout();
      throw new Error('Session expired. Please log in again.');
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `Request failed with status ${res.status}`);
    }
    return data;
  };

  return (
    <AuthContext.Provider value={{
      token,
      user,
      setUser,
      theme,
      setTheme,
      login,
      signup,
      logout,
      apiFetch,
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
