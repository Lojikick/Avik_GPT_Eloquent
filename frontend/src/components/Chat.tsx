'use client';

import React, { useState, useEffect, useRef} from 'react';
import { apiService } from '../lib/api';
import Prompt from '@/components/Prompt';
import Response from '@/components/Prompt';
import { Message } from '@/types/message';

interface ChatProps {
    currentSessionId: string | null;
    initialMessage?: string | null; // Add this
    onMessageSent?: () => void; // Add this to clear initial message
}

const Chat: React.FC<ChatProps> = ({
    currentSessionId, 
    initialMessage,
    onMessageSent
  }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Ref for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom function
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const loadChatHistory = async (sessionId: string) => {
    try {
      const response = await apiService.getChatHistory(sessionId, 50);
      
      setMessages(response.messages);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  useEffect(() => {
    if (initialMessage && initialMessage.trim()) {
        setInputValue(initialMessage);
    }
  }, [initialMessage]);

// Separate useEffect to auto-submit when inputValue changes from initial message
   useEffect(() => {
    if (initialMessage && inputValue === initialMessage && inputValue.trim()) {
        handleSubmit({ preventDefault: () => {} } as React.FormEvent);
        if (onMessageSent) {
        onMessageSent();
        }
    }
    }, [inputValue, initialMessage]);

  // Load history when session changes
  useEffect(() => {
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    }
  }, [currentSessionId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const messageContent = inputValue.trim();

    const userMessage: Message = {
        id: `user-${Date.now()}`,
        type: 'user',
        content: messageContent,
        timestamp: Date.now()
    }

    setMessages(prev => [...prev, userMessage]);
    

    const aiMessageId = `ai-${Date.now()}`;
    const loadingMessage: Message = {
        id: aiMessageId,
        type: 'ai',
        content: '',
        timestamp: Date.now(),
        isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);

    setInputValue("")
    setIsLoading(true);
    
    try {
      const result = await apiService.sendPrompt(inputValue, currentSessionId!);
      setMessages(prev => 
        prev.map(msg => 
          msg.id === aiMessageId 
            ? { ...msg, content: result.llm_response, isLoading: false }
            : msg
        )
      );
      
    } catch (error) {
        console.error('Error:', error);
    
        // Update the AI message with error and remove loading
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
    <div className='h-screen flex flex-col max-w-4xl mx-auto text-black'>
        <h1 className='text-center text-2xl font-bold py-4 flex-shrink-0'>AvikGPT</h1>

        {/* Messages Container - Single scrollable area */}
        <div 
            ref={messagesContainerRef}
            className='flex-1 overflow-y-auto space-y-4 px-4'
        >
                {messages.length === 0 ? (
                    <div className='flex items-center justify-center h-64 text-gray-500'>
                        <p>Start a conversation...</p>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div key={message.id}>
                            {message.type === 'user' ? (
                                <div className='flex justify-end'>
                                    <div className='max-w-xs lg:max-w-md px-4 py-2 bg-purple-500 text-white rounded-2xl rounded-br-md'>
                                        <p>{message.content}</p>
                                    </div>
                                </div>
                            ) : (
                                <div className='flex justify-start'>
                                    <div className='max-w-xs lg:max-w-2xl px-4 py-2 bg-gray-100 text-gray-800 rounded-2xl rounded-bl-md'>
                                        {message.isLoading ? (
                                        <p className='text-gray-500'>Thinking...</p>
                                        ) : (
                                        <p className='whitespace-pre-wrap'>{message.content}</p>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
                {/* Invisible div to scroll to */}
                <div ref={messagesEndRef} />
            </div>

        {/* Input Form - Fixed at bottom */}
        <div className='flex-shrink-0 border-t bg-white p-4'>
            <form onSubmit={handleSubmit}>
                <div className='relative'>
                    <input
                    className='w-full p-3 pr-12 border rounded-full'
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    />
                    <button className='absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center disabled:bg-gray-400' type="submit" disabled={isLoading || !inputValue.trim()}>
                    
                    {isLoading ? (
                        <span className='text-xs'>•••</span>
                    ) : (
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