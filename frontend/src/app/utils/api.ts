/**
 * SignVista API Utility
 * Handles communication with the FastAPI backend.
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ApiService {
    private sessionId: string;

    constructor() {
        // Default session ID
        this.sessionId = 'temp_guest';

        // Only access localStorage in the browser
        if (typeof window !== 'undefined') {
            const stored = localStorage.getItem('signvista_session_id');
            if (stored) {
                this.sessionId = stored;
            } else {
                this.sessionId = 'user_' + Math.random().toString(36).substring(2, 11);
                localStorage.setItem('signvista_session_id', this.sessionId);
            }
        }
    }

    getSessionId() {
        return this.sessionId;
    }

    async get(endpoint: string) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }

    async post(endpoint: string, data: any) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }

    // Feature Endpoints
    async translateText(text: string, language: string = 'en') {
        return this.post('/text-to-sign', { text, language });
    }

    async recognizeFrame(frame: string) {
        return this.post('/recognize-frame', { sessionId: this.sessionId, frame });
    }

    async getARLandmarks(frame: string) {
        return this.post('/ar/landmarks', { sessionId: this.sessionId, frame });
    }

    async getDashboard() {
        return this.get(`/dashboard/${this.sessionId}`);
    }

    async getDictionary(search?: string, category?: string, difficulty?: string) {
        let url = '/dictionary';
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);
        if (difficulty) params.append('difficulty', difficulty);

        const query = params.toString();
        if (query) url += `?${query}`;

        return this.get(url);
    }

    async getProgress() {
        return this.get(`/progress/${this.sessionId}`);
    }

    async getHistory() {
        return this.get(`/history/${this.sessionId}`);
    }

    async getAchievements() {
        return this.get(`/achievements/${this.sessionId}`);
    }

    async getProfile() {
        return this.get(`/profile/${this.sessionId}`);
    }

    async updateProfile(name: string, email: string, phone: string = '') {
        return this.post('/profile', {
            sessionId: this.sessionId,
            name,
            email,
            phone,
            preferred_language: 'en'
        });
    }

    // Chat Endpoints
    async getContacts() {
        return this.get('/chat/contacts');
    }

    async getChatMessages(contactId: string) {
        return this.get(`/chat/messages/${contactId}`);
    }

    async sendChatMessage(receiverId: string, content: string, type: string = 'text') {
        const id = 'msg_' + Math.random().toString(36).substring(2, 11);
        return this.post('/chat/send', {
            id,
            sender_id: 'me',
            receiver_id: receiverId,
            content,
            timestamp: Date.now() / 1000,
            type
        });
    }
}

export const api = new ApiService();
