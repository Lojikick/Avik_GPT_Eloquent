'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { apiService } from '../lib/api';
import Homepage from '../components/Homepage';
import Chat from '../components/Chat';
import GuestBanner from '../components/GuestBanner'; // Add this import

type ViewType = 'homepage' | 'chat';

const MainApp: React.FC = () => {
  const { userId, isAnonymous } = useAuth();

  const [currentView, setCurrentView] = useState<ViewType>('homepage');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);
  const [refreshSidebar, setRefreshSidebar] = useState(0);

  // Handle navigation to homepage
  const handleHomeSelect = () => {
    setCurrentView('homepage');
    setCurrentSessionId(null);
  };

  // Handle session selection
  const handleSessionSelect = (sessionId: string | null) => {
    setCurrentSessionId(sessionId);
    setCurrentView('chat');
  };

  // Handle new chat creation
  const handleNewChat = async (inputValue?: string) => {
    try {
      // For anonymous users, this will reuse/reset existing session
    //   if (isAnonymous) {
        // const confirmReplace = window.confirm(
        //   "As a guest, you can only have one active chat. Starting a new chat will replace your current one. Continue?"
        // );
    //     if (!confirmReplace) return;
    //   }

      const newSessionId = await apiService.createNewSession(userId);
      
      console.log("Session ID:", newSessionId);
      setCurrentSessionId(newSessionId);
      setRefreshSidebar(prev => prev + 1);
      setCurrentView('chat');
      setInitialMessage(inputValue || null);
    } catch (error) {
      console.error("Error creating session:", error);
    }
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        currentSessionId={currentSessionId}
        currentView={currentView}
        onSessionSelect={handleSessionSelect}
        onHomeSelect={handleHomeSelect}
        refreshTrigger={refreshSidebar}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Guest Banner */}
        <GuestBanner />
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {currentView === 'homepage' ? (
            <Homepage onNewChatClick={handleNewChat} />
          ) : (
            <Chat 
              currentSessionId={currentSessionId}
              initialMessage={initialMessage}
              onMessageSent={() => setInitialMessage(null)}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default MainApp;