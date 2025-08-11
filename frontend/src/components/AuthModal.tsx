import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Props interface - controls modal behavior and callbacks
interface AuthModalProps {
  isOpen: boolean;                           // Controls modal visibility
  onClose: () => void;                       // Callback to close modal
  onSuccess?: () => void;                    // Optional callback after successful auth
  defaultMode?: 'login' | 'register';       // Which form to show initially
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess, defaultMode = 'login' }) => {
  // Modal state management
  const [mode, setMode] = useState<'login' | 'register'>(defaultMode);  // Current form mode
  const [formData, setFormData] = useState({                            // All form input values
    email: '',
    password: '',
    name: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);                    // API call loading state
  const [error, setError] = useState('');                              // Error message display

  // Get authentication functions from context
  const { login, register } = useAuth();

  // Don't render modal if not open
  if (!isOpen) return null;

  // Handle input field changes and clear errors
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user starts typing
  };

  // Validate form data before submission
  const validateForm = () => {
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      return false;
    }

    // Additional validation for registration mode
    if (mode === 'register') {
      if (!formData.name) {
        setError('Name is required');
        return false;
      }
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match');
        return false;
      }
      if (formData.password.length < 6) {
        setError('Password must be at least 6 characters');
        return false;
      }
    }

    return true;
  };

  // Handle form submission for both login and register
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setError('');

    try {
      if (mode === 'login') {
        await login(formData.email, formData.password);
      } else {
        await register(formData.email, formData.password, formData.name);
      }
      onClose(); // Close modal on success

      // Execute success callback if provided (e.g., navigate to homepage)
      if (onSuccess) {
        onSuccess();
      }
      
    } catch (error: any) {
      // Display API error or generic message
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // Switch between login and register modes
  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    // Clear form data when switching modes
    setFormData({
      email: '',
      password: '',
      name: '',
      confirmPassword: ''
    });
  };

  return (
    // Modal overlay - covers entire screen with semi-transparent background
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      {/* Modal content container */}
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        {/* Modal header with title and close button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          {/* X button to close modal */}
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Error message display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Authentication form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name field - only shown in register mode */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter your full name"
                required
              />
            </div>
          )}

          {/* Email field - always shown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          {/* Password field - always shown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          {/* Confirm password field - only shown in register mode */}
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Confirm your password"
                required
              />
            </div>
          )}

          {/* Submit button with loading state */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              // Loading spinner and text
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {mode === 'login' ? 'Signing In...' : 'Creating Account...'}
              </span>
            ) : (
              // Normal button text
              mode === 'login' ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        {/* Toggle between login and register modes */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            {mode === 'login' ? "Don't have an account?" : "Already have an account?"}
            <button
              onClick={switchMode}
              className="ml-1 text-purple-600 hover:text-purple-700 font-medium"
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        {/* Benefits section - only shown in register mode */}
        {mode === 'register' && (
          <div className="mt-6 bg-purple-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-purple-800 mb-2">Why create an account?</h3>
            <ul className="text-sm text-purple-700 space-y-1">
              <li>• Save your chat history</li>
              <li>• Create multiple conversations</li>
              <li>• Access from any device</li>
              <li>• Never lose your chats</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;