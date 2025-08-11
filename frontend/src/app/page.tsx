'use client';
import React, { useState } from 'react';
import { AuthProvider } from '../contexts/AuthContext';
import MainApp from '../components/MainApp';

// Root page component - handles app-wide state reset on logout
export default function Home() {
  // Key that changes to force complete re-render of MainApp
  const [appKey, setAppKey] = useState(0);

  // Callback function passed to AuthProvider to handle logout cleanup, resets to Homepage when the user logs out
  const handleLogout = () => {
    setAppKey(prev => prev + 1);
  };

  return (
    // Wrap entire app with authentication context
    <AuthProvider onLogout={handleLogout}>
      <MainApp key={appKey} />
    </AuthProvider>
  );
}