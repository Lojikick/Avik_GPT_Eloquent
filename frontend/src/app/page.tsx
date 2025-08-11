'use client';
import React, { useState } from 'react';
import { AuthProvider } from '../contexts/AuthContext';
import MainApp from '../components/MainApp';

export default function Home() {
  const [appKey, setAppKey] = useState(0); // Force re-render on logout

  const handleLogout = () => {
    // Force complete app re-render to reset all state
    setAppKey(prev => prev + 1);
  };

  return (
    <AuthProvider onLogout={handleLogout}>
      <MainApp key={appKey} />
    </AuthProvider>
  );
}