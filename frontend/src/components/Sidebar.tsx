import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../lib/api';
import AuthModal from './AuthModal';

interface ChatSession {
  session_id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

interface SidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string | null) => void;
  onHomeSelect: () => void;
  currentView: 'homepage' | 'chat';
  refreshTrigger: number;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  currentSessionId, 
  onSessionSelect, 
  onHomeSelect, 
  currentView,
  refreshTrigger
}) => {
  const { user, userId, isAnonymous, logout } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Load user's chat sessions
  const loadSessions = async () => {
    if (!userId) return;
    
    setIsLoading(true);
    try {
      const response = await apiService.getUserSessions(userId);
      setSessions(response.sessions.slice(0, 10));
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [refreshTrigger, userId]);

  const handleAuthSuccess = () => {
    setShowAuthModal(false);
    onHomeSelect(); // Navigate to homepage
  };

  const handleNewChat = () => {
    onHomeSelect();
  };

  const handleLogout = async () => {
    try {
      await logout();
      setShowUserMenu(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <div className="w-64 bg-gray-50 h-screen flex flex-col border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800">AvikGPT</h1>
        {isAnonymous ? (
          <p className="text-xs text-gray-500">Guest Mode</p>
        ) : (
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center justify-between w-full text-left text-sm text-gray-600 hover:text-gray-800 mt-1"
            >
              <span className="truncate">{user?.name || user?.email}</span>
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showUserMenu && (
              <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 z-10">
                <div className="p-2">
                  <div className="px-3 py-2 text-xs text-gray-500 border-b">
                    {user?.email}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={handleNewChat}
          className="w-full bg-purple-600 text-white px-3 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center"
        >
          <span className="mr-2">+</span>
          New Chat
        </button>
      </div>

      {/* Recent Chats */}
      <div className="flex-1 overflow-y-auto p-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 px-3">
          {isAnonymous ? 'Your Chat (Guest)' : 'Recent Chats'}
        </h3>
        
        {isLoading ? (
          <div className="text-center text-gray-500 py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600 mx-auto"></div>
            <p className="text-sm mt-2">Loading chats...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center text-gray-500 py-4">
            <p className="text-sm">No chats yet</p>
            <p className="text-xs">Start a conversation!</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => onSessionSelect(session.session_id)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                  currentSessionId === session.session_id
                    ? 'bg-purple-100 text-purple-800 border-l-4 border-purple-500'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="font-medium text-sm truncate">{session.title}</div>
                <div className="text-xs text-gray-500 truncate">
                  {session.message_count} messages
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {isAnonymous && (
        <div className="p-3 border-t border-gray-200">
          <button
            onClick={() => setShowAuthModal(true)}
            className="w-full text-left px-3 py-2 rounded-lg text-purple-600 hover:bg-purple-50 transition-colors text-sm font-medium"
          >
            🔐 Sign up to save chats
          </button>
        </div>
      )}

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
        defaultMode="register"
      />
    </div>
  );
};

export default Sidebar;