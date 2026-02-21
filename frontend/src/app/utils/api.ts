/**
 * SignVista API Utility
 * Handles communication with the FastAPI backend.
 */

const getBackendOrigin = () => {
    if (typeof window !== 'undefined') {
        return `${window.location.hostname}:8001`;
    }
    return 'localhost:8001';
};

const HOST = getBackendOrigin();
export const BACKEND_ORIGIN = `http://${HOST}`;
export const WS_ORIGIN = `ws://${HOST}`;
export const API_BASE_URL = `${BACKEND_ORIGIN}/api`;

class ApiService {
    private sessionId: string;
    private token: string | null = null;

    constructor() {
        // Default values
        this.sessionId = 'temp_guest';

        // Only access localStorage in the browser
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('signvista_access_token');
            const storedSession = localStorage.getItem('signvista_session_id');

            if (storedSession) {
                this.sessionId = storedSession;
            } else {
                this.sessionId = 'user_' + Math.random().toString(36).substring(2, 11);
                localStorage.setItem('signvista_session_id', this.sessionId);
            }
        }
    }

    getSessionId() {
        return this.sessionId;
    }

    private async handleResponse(response: Response, endpoint: string) {
        if (response.status === 401) {
            // Don't redirect if we are already trying to login or register
            if (endpoint.includes('/auth/login') || endpoint.includes('/auth/register')) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Invalid credentials');
            }

            // Unauthorized - token is likely invalid or expired for other protected routes
            this.setSession('guest_' + Math.random().toString(36).substring(2, 11), null);
            if (typeof window !== 'undefined') {
                window.location.href = '/auth';
            }
            throw new Error('Unauthorized - redirects to login');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.statusText}`);
        }
        return response.json();
    }

    async get(endpoint: string) {
        const headers: any = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
        return this.handleResponse(response, endpoint);
    }

    async post(endpoint: string, data: any) {
        const headers: any = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        return this.handleResponse(response, endpoint);
    }

    async put(endpoint: string, data: any) {
        const headers: any = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data)
        });
        return this.handleResponse(response, endpoint);
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

    async getMe() {
        return this.get(`/profile/${this.sessionId}`);
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

    // Community Endpoints
    async getCommunityFeed() {
        return this.get('/community/feed');
    }

    async createPost(content: string, tags: string[] = []) {
        return this.post('/community/post', {
            sessionId: this.sessionId,
            content,
            tags
        });
    }

    async likePost(postId: string) {
        return this.post('/community/like', {
            sessionId: this.sessionId,
            postId
        });
    }

    async getActiveUsers() {
        return this.get('/community/active-users');
    }

    // Auth Endpoints
    async login(phone: string, password: string) {
        const result = await this.post('/auth/login', { phone, password });
        if (result.status === 'ok') {
            this.setSession(result.sessionId, result.access_token);
        }
        return result;
    }

    async register(data: any) {
        const result = await this.post('/auth/register', data);
        if (result.status === 'ok') {
            this.setSession(result.sessionId, result.access_token);
        }
        return result;
    }

    async logout() {
        try {
            await this.post('/auth/logout', {});
        } finally {
            this.setSession('guest_' + Math.random().toString(36).substring(2, 11), null);
        }
    }

    private setSession(sessionId: string, token: string | null) {
        this.sessionId = sessionId;
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('signvista_session_id', sessionId);
            if (token) {
                localStorage.setItem('signvista_access_token', token);
            } else {
                localStorage.removeItem('signvista_access_token');
            }
        }
    }
}

export const api = new ApiService();
