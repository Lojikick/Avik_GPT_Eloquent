import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
    baseURL: "http://localhost:8000",    // Backend server URL
    headers: {
        'Content-Type': 'application/json',
    }
});

// Type definitions for API data structures

// Chat message structure (unused in current code but defined)
export interface ChatMessage {
    id: string;
    userPrompt: string;
    llm_response: string;
    timestamp: Date;
}

// Request payload for sending prompts
export interface PromptRequest {
    prompt: string;
    session_id: string;
}

// Response structure from prompt API
export interface PromptResponse {
    userPrompt: string;     // Echo of user's input
    llm_response: string;   // AI's response
}

// Centralized API service object - contains all backend communication functions
export const apiService = {

    // Basic connectivity test
    async testConnection(): Promise<{ message: string }> {
        const response = await api.get("/");
        return response.data;
    },

    // Send user message to AI and get response
    async sendPrompt(prompt: string, session_id: string): Promise<PromptResponse> {
        const response = await api.post<PromptResponse>(
            "api/chat/prompt", {prompt, session_id}
        );
        return response.data;
    },

    // Server health status check
    async healthCheck(): Promise<{ status: string; message: string }> {
        const response = await api.get('/health');
        return response.data;
    },

    // Retrieve message history for a specific chat session
    async getChatHistory(sessionId: string, limit: number = 50): Promise<any> {
        const response = await api.get(`/api/chat/messages/${sessionId}?limit=${limit}`);
        return response.data;
    },

    // Get all chat sessions for a user
    async getUserSessions(userId: string = "default_user"): Promise<any> {
        const response = await api.get(`/api/users/${userId}/sessions`);
        return response.data;
    },

    // Create new chat session for user
    async createNewSession(userId: string = "default_user"): Promise<any> {
        const response = await api.post('/api/sessions', { user_id: userId });
        return response.data.session_id;  // Return just the session ID
    },

    // Delete a specific chat session
    async deleteSession(sessionId: string): Promise<any> {
        const response = await api.delete(`/api/sessions/${sessionId}`);
        return response.data;
    },

    // Authentication: User login
    async login(email: string, password: string): Promise<any> {
        const response = await api.post('/api/auth/login', { email, password });
        return response.data;
    },

    // Authentication: User registration with optional anonymous user linking
    async register(email: string, password: string, name: string, anonymousUserId?: string): Promise<any> {
        const response = await api.post('/api/auth/register', { 
            email, 
            password, 
            name 
        }, {
            // Pass anonymous user ID as query parameter to link existing sessions
            params: anonymousUserId ? { anonymous_user_id: anonymousUserId } : {}
        });
        return response.data;
    },

    // Authentication: User logout
    async logout(): Promise<void> {
        await api.post('/api/auth/logout');
    },

    // Authentication: Get current user info (used to check auth status)
    async getCurrentUser(): Promise<any> {
        const response = await api.get('/api/auth/me');
        return response.data;
    }
};