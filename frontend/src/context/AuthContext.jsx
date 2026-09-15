import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api';

const AuthContext = createContext();

const TOKEN_KEY = 'aayur_sathi_token';
const LEGACY_TOKEN_KEY = 'aiia_token';

export const ROLE_LABELS = {
  admin: 'Institutional Administration',
  pi: 'Principal Investigator',
  coordinator: 'Study Coordinator',
  monitor: 'Clinical Monitor (CRA)',
  ethics_committee: 'Institutional Ethics Committee (IEC)',
  pharmacovigilance: 'Pharmacovigilance (NPvCC)',
  regulator: 'Drug Regulator & Inspectorate',
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    return localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY) || null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authApi.me()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(LEGACY_TOKEN_KEY);
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await authApi.login(email, password);
    const newToken = res.data.access_token;
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
    const meRes = await authApi.me();
    setUser(meRes.data);
    return meRes.data;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const getRoleLabel = (role) => {
    return ROLE_LABELS[role] || role || 'User';
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, getRoleLabel }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
