'use client';

import React, { useState, useEffect, useRef} from 'react';
import { apiService } from '../lib/api';
import { Message } from '@/types/message';

//Chat View - Allows users to interact with the chatbot, start new initialized conversations, and view their conversation history,
// Handles the transaction flow of: receive initial message → auto-send → load history → handle new messages → manage loading states → auto-scroll

// Props interface - manages chat session and initial message handling
interface ChatProps {
    currentSessionId: string | null;    // Active chat session ID
    initialMessage?: string | null;     // Message to auto-send when chat opens
    onMessageSent?: () => void;         // Callback to clear initial message after sending
}

const Chat: React.FC<ChatProps> = ({
    currentSessionId, 
    initialMessage,
    onMessageSent
  }) => {
  // Core chat state
  const [messages, setMessages] = useState<Message[]>([]);     // All messages in current chat
  const [inputValue, setInputValue] = useState('');           // Current input field value
  const [isLoading, setIsLoading] = useState(false);          // Show loading state during API calls
  
  // References for auto-scrolling functionality
  const messagesEndRef = useRef<HTMLDivElement>(null);        // Invisible div at bottom of messages
  const messagesContainerRef = useRef<HTMLDivElement>(null);  // Scrollable messages container
  
  // Streaming text state
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Smoothly scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Auto-scroll when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Load chat history for a specific session
  const loadChatHistory = async (sessionId: string) => {
    try {
      const response = await apiService.getChatHistory(sessionId, 50);
      setMessages(response.messages);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  // Set input value when initial message is provided (from Homepage)
  useEffect(() => {
    if (initialMessage && initialMessage.trim()) {
        setInputValue(initialMessage);
    }
  }, [initialMessage]);

  // Load chat history when session changes
  useEffect(() => {
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    }
  }, [currentSessionId]);

  // Streaming text animation function
  const animateText = (messageId: string, fullText: string) => {
    let currentIndex = 0;
    setStreamingMessageId(messageId);
    
    const typeNextCharacter = () => {
      if (currentIndex < fullText.length) {
        const currentText = fullText.substring(0, currentIndex + 1);
        
        setMessages(prev => 
          prev.map(msg => 
            msg.id === messageId 
              ? { ...msg, content: currentText, isLoading: false }
              : msg
          )
        );
        
        currentIndex++;
        
        // Variable speed: slower for punctuation, faster for regular characters
        const char = fullText[currentIndex - 1];
        const delay = char === '.' || char === '!' || char === '?' ? 60 : 
                     char === ',' || char === ';' ? 40 : 
                     char === ' ' ? 15 : 10;
        
        streamingTimeoutRef.current = setTimeout(typeNextCharacter, delay);
      } else {
        // Animation complete
        setStreamingMessageId(null);
        streamingTimeoutRef.current = null;
      }
    };
    
    typeNextCharacter();
  };

  // Clean up timeout on component unmount
  useEffect(() => {
    return () => {
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
    };
  }, []);

  // Handle form submission and API communication
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const messageContent = inputValue.trim();

    // Create and add user message to chat
    const userMessage: Message = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: messageContent,
        timestamp: Date.now()
    }

    setMessages(prev => [...prev, userMessage]);
    

    // Create placeholder AI message with loading state
    const aiMessageId = `ai-${Date.now()}`;
    const loadingMessage: Message = {
        id: aiMessageId,
        type: 'ai',
        content: '',
        timestamp: Date.now(),
        isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);

    setInputValue("") // Clear input immediately
    setIsLoading(true);
    
    try {
      // Send message to API and get AI response
      const result = await apiService.sendPrompt(inputValue, currentSessionId!);
      
      // Start streaming animation instead of immediate update
      animateText(aiMessageId, result.llm_response);
      
    } catch (error) {
        console.error('Error:', error);
    
        // Update loading message with error message (no animation for errors)
        setMessages(prev => 
          prev.map(msg => 
            msg.id === aiMessageId 
              ? { ...msg, content: 'Sorry, there was an error processing your request.', isLoading: false }
              : msg
          )
        );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex flex-col h-full w-full max-w-4xl mx-auto text-black'>
        {/* Fixed header */}
        <div className='flex-shrink-0 py-4 border-b border-gray-200'>
            <h1 className='text-center text-2xl font-bold'>AvikGPT</h1>
        </div>

        {/* Scrollable messages area - takes remaining space */}
        <div 
            ref={messagesContainerRef}
            className='flex-1 overflow-y-auto px-4 py-4 min-h-0'
        >
            <div className='space-y-4'>
                {/* Show placeholder when no messages */}
                {messages.length === 0 ? (
                    <div className='flex items-center justify-center h-64 text-gray-500'>
                        <p>Start a conversation...</p>
                    </div>
                ) : (
                    // Render all messages
                    messages.map((message) => (
                        <div key={message.id}>
                            {message.type === 'user' ? (
                                // User message - right-aligned, purple background, consistent max width
                                <div className='flex justify-end'>
                                    <div className='max-w-md px-4 py-2 bg-purple-500 text-white rounded-2xl rounded-br-md'>
                                        <p className='break-words'>{message.content}</p>
                                    </div>
                                </div>
                            ) : (
                                // AI message - left-aligned, gray background, consistent max width
                                <div className='flex justify-start'>
                                    <div className='max-w-2xl px-4 py-2 bg-gray-100 text-gray-800 rounded-2xl rounded-bl-md'>
                                        {message.isLoading ? (
                                            <p className='text-gray-500'>Thinking...</p>
                                        ) : (
                                            <div className='whitespace-pre-wrap break-words'>
                                                {message.content}
                                                {/* Add blinking cursor during streaming */}
                                                {streamingMessageId === message.id && (
                                                    <span className='animate-pulse ml-1 text-gray-400'>|</span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
                {/* Invisible element to enable auto-scroll */}
                <div ref={messagesEndRef} />
            </div>
        </div>

        {/* Fixed input form at bottom */}
        <div className='flex-shrink-0 border-t border-gray-200 bg-white p-4'>
            <form onSubmit={handleSubmit}>
                <div className='relative'>
                    {/* Message input field */}
                    <input
                    className='w-full p-3 pr-12 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    />
                    {/* Send button - disabled when loading or input empty */}
                    <button 
                        className='absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center disabled:bg-gray-400 transition-colors' 
                        type="submit" 
                        disabled={isLoading || !inputValue.trim()}
                    >
                        {isLoading ? (
                            // Loading indicator
                            <span className='text-xs'>•••</span>
                        ) : (
                            // Send arrow icon
                            <svg className='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 10l7-7m0 0l7 7m-7-7v18' />
                            </svg>
                        )}
                    </button>
                </div>
            </form>
        </div>
    </div>
  );
};

export default Chat;