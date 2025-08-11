import axios from 'axios';

const api = axios.create({
    baseURL: "http://localhost:8000",
    headers: {
        'Content-Type': 'application/json',
    }
});


export interface ChatMessage {
    id: string;
    userPrompt: string;
    llm_response: string;
    timestamp: Date;
}

export interface PromptRequest {
    prompt: string;
    session_id: string;
  }
  
export interface PromptResponse {
userPrompt: string;
llm_response: string;
}

// API functions
export const apiService = {

    // Test the connection
    async testConnection(): Promise<{ message: string }> {
        const response = await api.get("/");
        return response.data;
    },

    // Send a chat prompt
    async sendPrompt(prompt: string, session_id: string): Promise<PromptResponse> {
        const response = await api.post<PromptResponse>(
            "api/chat/prompt", {prompt, session_id}
        );
        return response.data;
    },

    // Health check
    async healthCheck(): Promise<{ status: string; message: string }> {
        const response = await api.get('/health');
        return response.data;
    },

    // Get chat history 
    async getChatHistory(sessionId: string, limit: number = 50): Promise<any> {
        const response = await api.get(`/api/chat/messages/${sessionId}?limit=${limit}`);
        return response.data;
    },

    async getUserSessions(userId: string = "default_user"): Promise<any> {
    const response = await api.get(`/api/users/${userId}/sessions`);
    return response.data;
  },

  async createNewSession(userId: string = "default_user"): Promise<any> {
    const response = await api.post('/api/sessions', { user_id: userId });
    return response.data.session_id;
  },

  async deleteSession(sessionId: string): Promise<any> {
    const response = await api.delete(`/api/sessions/${sessionId}`);
    return response.data;
  },

  async login(email: string, password: string): Promise<any> {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  async register(email: string, password: string, name: string, anonymousUserId?: string): Promise<any> {
    const response = await api.post('/api/auth/register', { 
      email, 
      password, 
      name 
    }, {
      params: anonymousUserId ? { anonymous_user_id: anonymousUserId } : {}
    });
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post('/api/auth/logout');
  },

  async getCurrentUser(): Promise<any> {
    const response = await api.get('/api/auth/me');
    return response.data;
  }
};


