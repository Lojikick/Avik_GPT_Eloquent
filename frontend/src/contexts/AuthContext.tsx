'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../lib/api';

interface User {
  user_id: string;
  email: string;
  name: string;
  user_type: 'anonymous' | 'registered';
}

interface AuthContextType {
  user: User | null;
  userId: string;
  userType: 'anonymous' | 'registered';
  isAnonymous: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ 
  children: React.ReactNode;
  onLogout?: () => void; // Accept logout callback
}> = ({ children, onLogout }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      // Not authenticated, create anonymous user
      createAnonymousUser();
    } finally {
      setIsLoading(false);
    }
  };

  const createAnonymousUser = () => {
    let anonymousId = localStorage.getItem('anonymous_user_id');
    
    if (!anonymousId) {
      anonymousId = `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('anonymous_user_id', anonymousId);
    }
    
    setUser({
      user_id: anonymousId,
      email: '',
      name: 'Guest',
      user_type: 'anonymous'
    });
  };

  const login = async (email: string, password: string) => {
    const userData = await apiService.login(email, password);
    setUser(userData);
    localStorage.removeItem('anonymous_user_id'); // Clear anonymous ID
  };

  const register = async (email: string, password: string, name: string) => {
    let anonymousId = localStorage.getItem('anonymous_user_id');
    const userData = await apiService.register(email, password, name, anonymousId!);
    setUser(userData);
    localStorage.removeItem('anonymous_user_id'); // Clear anonymous ID
  };

  const logout = async () => {
    await apiService.logout();
    setUser(null);
    createAnonymousUser(); // Create new anonymous user
    
    // Trigger logout callback to navigate home
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      userId: user?.user_id || '',
      userType: user?.user_type || 'anonymous',
      isAnonymous: user?.user_type === 'anonymous',
      login,
      register,
      logout,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};