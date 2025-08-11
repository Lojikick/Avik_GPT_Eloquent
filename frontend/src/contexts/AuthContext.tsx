'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../lib/api';

// AuthContext - Houses all content regarding user authentication (For both anonymous and registered users) and global variables such as userID utilized in other components

// User data structure - represents both registered and anonymous users
interface User {
  user_id: string;
  email: string;
  name: string;
  user_type: 'anonymous' | 'registered';
}

// Authentication context interface - defines all auth methods and state
interface AuthContextType {
  user: User | null;                    // Current user object or null
  userId: string;                       // Quick access to user ID
  userType: 'anonymous' | 'registered'; // Quick access to user type
  isAnonymous: boolean;                 // Helper to check if user is anonymous
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;                   // Shows if auth check is in progress
}

// Create React context for authentication state
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Main authentication provider component
export const AuthProvider: React.FC<{ 
  children: React.ReactNode;
  onLogout?: () => void; // Optional callback when user logs out
}> = ({ children, onLogout }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status when component mounts
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Verify if user is authenticated, create anonymous user if not
  const checkAuthStatus = async () => {
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData); // User is authenticated
    } catch (error) {
      // Not authenticated, create anonymous user session
      createAnonymousUser();
    } finally {
      setIsLoading(false); // Stop loading spinner
    }
  };

  // Generate or retrieve anonymous user ID from localStorage
  const createAnonymousUser = () => {
    let anonymousId = localStorage.getItem('anonymous_user_id');
    
    // Create new anonymous ID if none exists
    if (!anonymousId) {
      anonymousId = `anon_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('anonymous_user_id', anonymousId);
    }
    
    // Set anonymous user in state
    setUser({
      user_id: anonymousId,
      email: '',
      name: 'Guest',
      user_type: 'anonymous'
    });
  };

  // Authenticate user with email/password
  const login = async (email: string, password: string) => {
    const userData = await apiService.login(email, password);
    setUser(userData);
    localStorage.removeItem('anonymous_user_id'); // Clean up anonymous session
  };

  // Register new user account, linking to anonymous session if exists
  const register = async (email: string, password: string, name: string) => {
    let anonymousId = localStorage.getItem('anonymous_user_id');
    const userData = await apiService.register(email, password, name, anonymousId!);
    setUser(userData);
    localStorage.removeItem('anonymous_user_id'); // Clean up anonymous session
  };

  // Log out user and create new anonymous session
  const logout = async () => {
    await apiService.logout();
    setUser(null);
    createAnonymousUser(); // Start fresh anonymous session
    
    // Execute optional navigation callback
    if (onLogout) {
      onLogout();
    }
  };

  // Provide authentication context to child components
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

// Custom hook to access authentication context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};