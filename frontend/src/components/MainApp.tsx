'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { apiService } from '../lib/api';
import Homepage from '../components/Homepage';
import Chat from '../components/Chat';
import GuestBanner from '../components/GuestBanner';

// MainApp - Houses all of the components that the user interacts with, the webapp design uses a Sidebar that the user always sees, 
// and a main page which either houses the Homepage or the Chat view. The Homepage is an interface to allow users to start a new chat,
// and the Chat view allows users to have full conversations with the chatbot, 

//The web_app uses sessions to organize conversations. A user's chat session will be created, and its contents continuously updated and stored via API calls to the database
//Sessions are retrieved via a session id, which is passed into the Chat component to display any of the users sessions. 

//If the user is logged in, the Sidebar will house references 
// to the recent sessions the user interacted with, and will route users to a Chat view (by passing in the said session id) with the respective session contents

//If the user is not logged in, they will be treated as a guest and only be allowed to interact with one session, if they log in their chat data will be moved to their account.


// Define possible app views - either homepage or chat interface
type ViewType = 'homepage' | 'chat';

const MainApp: React.FC = () => {
  // Get authentication info from context
  const { userId, isAnonymous } = useAuth();

  // Core app state management
  const [currentView, setCurrentView] = useState<ViewType>('homepage');      // Which view to show
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null); // Active chat session
  const [initialMessage, setInitialMessage] = useState<string | null>(null);     // Message to send when chat opens
  const [refreshSidebar, setRefreshSidebar] = useState(0);                       // Trigger sidebar refresh

  // Navigate back to homepage and clear active session
  const handleHomeSelect = () => {
    setCurrentView('homepage');
    setCurrentSessionId(null);
  };

  // Switch to chat view with specific session
  const handleSessionSelect = (sessionId: string | null) => {
    setCurrentSessionId(sessionId);
    setCurrentView('chat');
  };

  // Create new chat session and switch to chat view
  const handleNewChat = async (inputValue?: string) => {
    try {
      // Optional: Warn anonymous users about session replacement
      // (Currently commented out - anonymous users can create multiple sessions)
      
      // Create new session via API
      const newSessionId = await apiService.createNewSession(userId);
      
      console.log("Session ID:", newSessionId);
      setCurrentSessionId(newSessionId);               // Set as active session
      setRefreshSidebar(prev => prev + 1);            // Trigger sidebar update
      setCurrentView('chat');                         // Switch to chat view
      setInitialMessage(inputValue || null);          // Store message to send
    } catch (error) {
      console.error("Error creating session:", error);
    }
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left sidebar - shows chat history and navigation */}
      <Sidebar
        currentSessionId={currentSessionId}
        currentView={currentView}
        onSessionSelect={handleSessionSelect}
        onHomeSelect={handleHomeSelect}
        refreshTrigger={refreshSidebar}  // Forces sidebar to refresh when incremented
      />

      {/* Right side - main content area */}
      <div className="flex-1 flex flex-col">
        {/* Show banner for guest users */}
        <GuestBanner />
        
        {/* Main content - conditionally render homepage or chat */}
        <div className="flex-1 flex flex-col min-h-0">
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