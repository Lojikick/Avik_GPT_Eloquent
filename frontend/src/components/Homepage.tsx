import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import AuthModal from './AuthModal';

interface HomepageProps {
  onNewChatClick?: (initialMessage?: string) => void;
}

const Homepage: React.FC<HomepageProps> = ({ onNewChatClick }) => {
  const [inputValue, setInputValue] = useState('');
  const { isAnonymous } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);

  const handleStartChat = () => {
    if (inputValue.trim() && onNewChatClick){
        onNewChatClick(inputValue.trim());
    }
    
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-white min-h-screen">
      {/* Welcome Section */}
      <div className="text-center mb-12 max-w-2xl">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Welcome
        </h1>
      </div>

      {isAnonymous && (
        <div className="mb-8 text-center bg-purple-50 rounded-xl p-6 max-w-md">
          <h3 className="text-lg font-semibold text-purple-800 mb-2">
            Unlock Full Features
          </h3>
          <p className="text-sm text-purple-600 mb-4">
            Create an account to save your conversations and access them from anywhere!
          </p>
          <button
            onClick={() => setShowAuthModal(true)}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Sign Up Free
          </button>
        </div>
      )}

      {/* Input Section */}
      <div className="w-full max-w-3xl">
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && inputValue.trim()) {
                handleStartChat()
              }
            }}
            placeholder="Ask anything"
            className="w-full px-4 py-4 pr-12 text-gray-700 bg-white border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm"
          />
          <button
            onClick={() => {
              if (inputValue.trim()) {
                handleStartChat()
              }
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 text-gray-400 hover:text-purple-600 transition-colors"
          >
            <svg 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="m22 2-7 20-4-9-9-4Z"/>
              <path d="M22 2 11 13"/>
            </svg>
          </button>
        </div>
      </div>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        defaultMode="register"
      />
      
    </div>
  );
};

export default Homepage;