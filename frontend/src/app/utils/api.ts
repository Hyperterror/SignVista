/**
 * SignVista API client.
 *
 * - HTTP calls go to same-origin `/api/*` (proxied to FastAPI by next.config.ts),
 *   so the HttpOnly auth cookie is first-party and sent automatically.
 * - WebSockets connect to the backend directly and authenticate with a
 *   short-lived ticket from POST /api/auth/ws-ticket.
 */

const API_BASE = '/api';

/** Prefix for sign media URLs returned by the API (served via the /assets proxy). */
export const BACKEND_ORIGIN = '';

export const getWsOrigin = (): string => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
        return process.env.NEXT_PUBLIC_WS_URL.replace(/\/$/, '');
    }
    if (typeof window === 'undefined') return 'ws://127.0.0.1:8000';
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const port = process.env.NEXT_PUBLIC_BACKEND_PORT || '8000';
    return `${proto}//${window.location.hostname}:${port}`;
};

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.status = status;
    }
}

export interface CurrentUser {
    sessionId: string;
    name: string;
    email: string;
    phone: string;
    preferred_language: string;
    created_at?: number;
}

const SESSION_KEY = 'signvista_session_id';
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/logout'];

function errorMessage(data: any, fallback: string): string {
    const detail = data?.detail;
    if (typeof detail === 'string') return detail;
    // FastAPI validation errors: [{loc, msg, ...}]
    if (Array.isArray(detail) && detail.length > 0) {
        return detail.map((d: any) => String(d.msg || '').replace(/^Value error, /, '')).join('. ');
    }
    return fallback;
}

class ApiService {
    private sessionId: string = '';
    private mePromise: Promise<CurrentUser> | null = null;

    constructor() {
        if (typeof window !== 'undefined') {
            this.sessionId = localStorage.getItem(SESSION_KEY) || '';
            // Clean up values written by older versions of the app
            localStorage.removeItem('signvista_access_token');
            if (/^(user|guest|temp)_/.test(this.sessionId)) this.sessionId = '';
        }
    }

    getSessionId(): string {
        return this.sessionId;
    }

    private setSession(sessionId: string) {
        this.sessionId = sessionId;
        if (typeof window !== 'undefined') {
            if (sessionId) localStorage.setItem(SESSION_KEY, sessionId);
            else localStorage.removeItem(SESSION_KEY);
        }
    }

    private handleUnauthorized() {
        this.setSession('');
        this.mePromise = null;
        if (typeof window !== 'undefined' && !['/', '/auth'].includes(window.location.pathname)) {
            const next = encodeURIComponent(window.location.pathname + window.location.search);
            // Clear the (invalid) cookie first so the route guard doesn't loop
            fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'same-origin' })
                // Not a React component, so no router here; a full navigation also resets client state
                // eslint-disable-next-line @next/next/no-location-assign-relative-destination
                .finally(() => { window.location.href = `/auth?next=${next}`; });
        }
    }

    private async request(method: string, endpoint: string, data?: unknown) {
        const init: RequestInit = { method, credentials: 'same-origin', headers: {} };
        if (data !== undefined) {
            (init.headers as Record<string, string>)['Content-Type'] = 'application/json';
            init.body = JSON.stringify(data);
        }

        let response: Response;
        try {
            response = await fetch(`${API_BASE}${endpoint}`, init);
        } catch {
            throw new ApiError('Cannot reach the server. Check your connection.', 0);
        }

        const body = await response.json().catch(() => ({}));
        if (response.status === 401 && !AUTH_ENDPOINTS.some((e) => endpoint.startsWith(e))) {
            this.handleUnauthorized();
            throw new ApiError('Your session has expired. Please sign in again.', 401);
        }
        if (!response.ok) {
            const fallback = response.status === 429
                ? 'Too many requests. Please slow down.'
                : `Request failed (${response.status})`;
            throw new ApiError(errorMessage(body, fallback), response.status);
        }
        return body;
    }

    get(endpoint: string) { return this.request('GET', endpoint); }
    post(endpoint: string, data: unknown = {}) { return this.request('POST', endpoint, data); }
    put(endpoint: string, data: unknown = {}) { return this.request('PUT', endpoint, data); }

    // ─── Auth ──────────────────────────────────────────────────

    async login(phone: string, password: string) {
        const result = await this.post('/auth/login', { phone, password });
        this.setSession(result.sessionId);
        this.mePromise = null;
        return result;
    }

    async register(data: { name: string; email: string; phone: string; password: string; preferred_language?: string }) {
        const result = await this.post('/auth/register', data);
        this.setSession(result.sessionId);
        this.mePromise = null;
        return result;
    }

    async logout() {
        try {
            await this.post('/auth/logout');
        } finally {
            this.setSession('');
            this.mePromise = null;
        }
    }

    /** Current user (cached per page load). */
    getMe(force = false): Promise<CurrentUser> {
        if (!this.mePromise || force) {
            this.mePromise = this.get('/auth/me').then((me: CurrentUser) => {
                this.setSession(me.sessionId);
                return me;
            }).catch((e) => {
                this.mePromise = null;
                throw e;
            });
        }
        return this.mePromise;
    }

    /** Resolves the user id, fetching it if this tab doesn't know it yet. */
    async ensureSessionId(): Promise<string> {
        if (this.sessionId) return this.sessionId;
        return (await this.getMe()).sessionId;
    }

    /** Authenticated WebSocket URL for a backend path such as `/api/ws/recognize`. */
    async getWsUrl(path: string): Promise<string> {
        const { ticket } = await this.post('/auth/ws-ticket');
        return `${getWsOrigin()}${path}?ticket=${encodeURIComponent(ticket)}`;
    }

    getRecognizeWsUrl() { return this.getWsUrl('/api/ws/recognize'); }
    getChatWsUrl() { return this.getWsUrl('/api/chat/ws'); }

    // ─── Translation / recognition ─────────────────────────────

    translateText(text: string, language: string = 'en') {
        return this.post('/text-to-sign', { text, language });
    }

    recognizeFrame(frame: string) {
        return this.post('/recognize-frame', { frame });
    }

    getARLandmarks(frame: string) {
        return this.post('/ar/landmarks', { frame });
    }

    getVocabulary() {
        return this.get('/vocabulary');
    }

    // ─── Learning ──────────────────────────────────────────────

    learnAttempt(targetWord: string, frame: string) {
        return this.post('/learn/attempt', { targetWord, frame });
    }

    async getDashboard() { return this.get(`/dashboard/${await this.ensureSessionId()}`); }
    async getProgress() { return this.get(`/progress/${await this.ensureSessionId()}`); }
    async getLearningPath() { return this.get(`/progress/${await this.ensureSessionId()}/next`); }
    async getHistory(limit = 20) { return this.get(`/history/${await this.ensureSessionId()}?limit=${limit}`); }
    async getAchievements() { return this.get(`/achievements/${await this.ensureSessionId()}`); }
    async getStats() { return this.get(`/stats/${await this.ensureSessionId()}`); }

    getDictionary(search?: string, category?: string, difficulty?: string) {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (category) params.append('category', category);
        if (difficulty) params.append('difficulty', difficulty);
        const query = params.toString();
        return this.get(`/dictionary${query ? `?${query}` : ''}`);
    }

    // ─── Game ──────────────────────────────────────────────────

    startGame(duration = 30) { return this.post('/game/start', { duration }); }
    gameAttempt(gameId: string, frame: string) { return this.post('/game/attempt', { gameId, frame }); }
    async getGameResult(gameId: string) {
        return this.get(`/game/result/${await this.ensureSessionId()}/${encodeURIComponent(gameId)}`);
    }

    // ─── Profile / settings / notifications ────────────────────

    async getProfile() { return this.get(`/profile/${await this.ensureSessionId()}`); }

    async updateProfile(name: string, email: string, phone: string = '', preferred_language: string = 'en') {
        const result = await this.post('/profile', { name, email, phone, preferred_language });
        this.mePromise = null;
        return result;
    }

    async getSettings() { return this.get(`/settings/${await this.ensureSessionId()}`); }
    updateSettings(settings: Record<string, unknown>) { return this.put('/settings', settings); }

    async getNotifications() { return this.get(`/notifications/${await this.ensureSessionId()}`); }
    markNotificationRead(id: number) { return this.post(`/notifications/read/${id}`); }
    markAllNotificationsRead() { return this.post('/notifications/read_all'); }

    // ─── Chat ──────────────────────────────────────────────────

    getContacts() { return this.get('/chat/contacts'); }
    getChatMessages(contactId: string) { return this.get(`/chat/messages/${encodeURIComponent(contactId)}`); }
    sendChatMessage(receiverId: string, content: string, type: 'text' | 'sign' = 'text') {
        return this.post('/chat/send', { receiver_id: receiverId, content, type });
    }

    // ─── Community ─────────────────────────────────────────────

    getCommunityFeed(offset = 0, limit = 20) { return this.get(`/community/feed?offset=${offset}&limit=${limit}`); }
    createPost(content: string, tags: string[] = []) { return this.post('/community/post', { content, tags }); }
    likePost(postId: string) { return this.post('/community/like', { postId }); }
    getComments(postId: string) { return this.get(`/community/posts/${encodeURIComponent(postId)}/comments`); }
    addComment(postId: string, content: string) {
        return this.post(`/community/posts/${encodeURIComponent(postId)}/comments`, { content });
    }
    getActiveUsers() { return this.get('/community/active-users'); }
}

export const api = new ApiService();
