"use client";

import { useState, useEffect, useEffectEvent, useRef } from 'react';
import { Search, Send, Plus, ChevronLeft, Sparkles } from 'lucide-react';
import { api } from '../utils/api';
import { nowSeconds } from '../utils/time';
import SignToolbox from '../components/chat/SignToolbox';
import { toast } from 'sonner';

interface Contact {
    id: string;
    name: string;
    status: string;
    last_message: string;
    last_message_time: number;
    unread_count?: number;
}

interface ChatMessage {
    id: string;
    sender_id: string;
    receiver_id: string;
    content: string;
    timestamp: number;
    type: string;
}

export default function ChatPage() {
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [isToolboxOpen, setIsToolboxOpen] = useState(true);
    const [isLoading, setIsLoading] = useState(true);
    const [isPickerOpen, setIsPickerOpen] = useState(false);
    const [activeUsers, setActiveUsers] = useState<{ user_id: string; name: string }[]>([]);
    const [search, setSearch] = useState('');
    const [sessionId, setSessionId] = useState(api.getSessionId());
    const chatEndRef = useRef<HTMLDivElement>(null);
    const ws = useRef<WebSocket | null>(null);
    const selectedRef = useRef<Contact | null>(null);

    useEffect(() => {
        selectedRef.current = selectedContact;
    }, [selectedContact]);

    const applyContacts = (data: Contact[], selectId?: string, selectName?: string) => {
        let list = data;
        if (selectId && !data.some((c) => c.id === selectId)) {
            list = [{ id: selectId, name: selectName || 'New chat', status: 'offline', last_message: '', last_message_time: nowSeconds() }, ...data];
        }
        setContacts(list);
        setSelectedContact((current) => {
            if (selectId) return list.find((c) => c.id === selectId) || current;
            return current ?? list[0] ?? null;
        });
    };

    const loadContacts = () => {
        api.getContacts()
            .then((data: Contact[]) => applyContacts(data))
            .catch((error: any) => toast.error(error.message || 'Failed to load contacts'));
    };

    // Called from the socket handler when a message arrives from a new contact
    const onUnknownContact = useEffectEvent(() => loadContacts());

    // Initial load (supports /chat?to=<userId>&name=<name> from the community page)
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        let ignore = false;
        api.ensureSessionId().then((id) => { if (!ignore) setSessionId(id); }).catch(() => { });
        api.getContacts()
            .then((data: Contact[]) => { if (!ignore) applyContacts(data, params.get('to') || undefined, params.get('name') || undefined); })
            .catch((error: any) => { if (!ignore) toast.error(error.message || 'Failed to load contacts'); })
            .finally(() => { if (!ignore) setIsLoading(false); });
        return () => { ignore = true; };
    }, []);

    // Authenticated WebSocket with reconnect
    useEffect(() => {
        let closedByUs = false;
        let retries = 0;
        let timer: ReturnType<typeof setTimeout> | null = null;

        const connect = async () => {
            let url: string;
            try {
                url = await api.getChatWsUrl();
            } catch {
                return;
            }
            if (closedByUs) return;
            const socket = new WebSocket(url);
            ws.current = socket;

            socket.onopen = () => { retries = 0; };

            socket.onmessage = (event) => {
                let msg: any;
                try {
                    msg = JSON.parse(event.data);
                } catch {
                    return;
                }
                if (msg.error) {
                    toast.error(msg.error);
                    return;
                }
                const current = selectedRef.current;
                const inThread = current && (msg.sender_id === current.id || msg.receiver_id === current.id);
                if (inThread) {
                    setMessages((prev) => (prev.some((m) => m.id === msg.id) ? prev : [...prev, msg]));
                }
                // Keep the sidebar previews (and new conversations) up to date
                setContacts((prev) => {
                    const otherId = msg.sender_id === api.getSessionId() ? msg.receiver_id : msg.sender_id;
                    const existing = prev.find((c) => c.id === otherId);
                    if (!existing) {
                        onUnknownContact();
                        return prev;
                    }
                    const updated = {
                        ...existing,
                        last_message: msg.content,
                        last_message_time: msg.timestamp,
                        unread_count: inThread ? 0 : (existing.unread_count || 0) + (msg.sender_id === otherId ? 1 : 0),
                    };
                    return [updated, ...prev.filter((c) => c.id !== otherId)];
                });
            };

            socket.onclose = (event) => {
                if (ws.current === socket) ws.current = null;
                if (closedByUs || event.code === 1008) return;
                if (retries < 6) timer = setTimeout(connect, 1000 * 2 ** retries++);
            };
        };

        connect();
        return () => {
            closedByUs = true;
            if (timer) clearTimeout(timer);
            const socket = ws.current;
            ws.current = null;
            if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) socket.close();
        };
    }, []);

    // Load history whenever the conversation changes
    const selectedId = selectedContact?.id;
    useEffect(() => {
        if (!selectedId) return;
        let cancelled = false;
        api.getChatMessages(selectedId)
            .then((data: ChatMessage[]) => {
                if (cancelled) return;
                setMessages(data);
                setContacts((prev) => prev.map((c) => (c.id === selectedId ? { ...c, unread_count: 0 } : c)));
            })
            .catch((e: any) => { if (!cancelled) toast.error(e.message || 'Failed to load messages'); });
        return () => { cancelled = true; };
    }, [selectedId]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const openPicker = async () => {
        setIsPickerOpen((open) => !open);
        try {
            const data = await api.getActiveUsers();
            setActiveUsers(data.users || []);
        } catch {
            setActiveUsers([]);
        }
    };

    const startConversation = (userId: string, name: string) => {
        setIsPickerOpen(false);
        const existing = contacts.find((c) => c.id === userId);
        if (existing) {
            setSelectedContact(existing);
            return;
        }
        const contact: Contact = { id: userId, name, status: 'online', last_message: '', last_message_time: nowSeconds() };
        setContacts((prev) => [contact, ...prev]);
        setSelectedContact(contact);
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        const content = newMessage.trim();
        if (!content || !selectedContact) return;
        if (selectedContact.id === 'official_bot') {
            toast.info("The SignVista Team account doesn't accept replies.");
            return;
        }
        setNewMessage('');

        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ receiver_id: selectedContact.id, content, type: 'text' }));
            return;
        }
        // HTTP fallback when the socket is reconnecting
        try {
            const msg = await api.sendChatMessage(selectedContact.id, content);
            setMessages((prev) => (prev.some((m) => m.id === msg.id) ? prev : [...prev, msg]));
        } catch (err: any) {
            setNewMessage(content);
            toast.error(err.message || 'Message could not be sent');
        }
    };

    const visibleContacts = contacts.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()));

    if (isLoading) return <div className="h-screen flex items-center justify-center font-bold text-[#105F68]">Initializing Secure Chat...</div>;

    // Filter messages for current thread view
    const threadMessages = messages.filter(m =>
        (m.sender_id === sessionId && m.receiver_id === selectedContact?.id) ||
        (m.sender_id === selectedContact?.id && m.receiver_id === sessionId)
    );

    return (
        <div className="chat-main h-[calc(100vh-2rem)] flex bg-white dark:bg-gray-900 rounded-[32px] shadow-2xl overflow-hidden border border-gray-100 dark:border-gray-800 m-4">
            {/* Sidebar: Conversations */}
            <div className={`w-80 border-r border-gray-100 dark:border-gray-800 flex flex-col bg-gray-50/30 dark:bg-gray-900/50 ${selectedContact ? 'hidden md:flex' : 'flex'}`}>
                <div className="p-6 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-black text-gray-900 dark:text-gray-100 tracking-tight">Messages</h2>
                        <button
                            onClick={openPicker}
                            title="Start a new conversation"
                            aria-label="Start a new conversation"
                            className="p-2 bg-[#105F68] text-white rounded-xl shadow-lg hover:scale-110 transition-transform"
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                    </div>
                    {isPickerOpen && (
                        <div className="mb-4 p-3 rounded-2xl bg-white dark:bg-gray-800 shadow-lg border border-gray-100 dark:border-gray-700">
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Online now</p>
                            {activeUsers.length === 0 ? (
                                <p className="text-sm text-gray-500">Nobody else is online right now. You can also message people from the Community page.</p>
                            ) : (
                                activeUsers.map((u) => (
                                    <button
                                        key={u.user_id}
                                        onClick={() => startConversation(u.user_id, u.name)}
                                        className="w-full text-left px-3 py-2 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-semibold"
                                    >
                                        {u.name}
                                    </button>
                                ))
                            )}
                        </div>
                    )}
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-[#105F68] transition-colors" />
                        <input
                            type="text"
                            placeholder="Search chats..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-11 pr-4 py-3 rounded-2xl bg-white dark:bg-gray-800 border-none shadow-sm focus:ring-2 focus:ring-[#105F68]/10 transition-all text-sm font-medium"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                    {visibleContacts.length === 0 && (
                        <p className="p-4 text-sm text-gray-500">No conversations yet. Press + to start one.</p>
                    )}
                    {visibleContacts.map((contact) => (
                        <button
                            key={contact.id}
                            onClick={() => setSelectedContact(contact)}
                            className={`w-full flex items-center gap-4 p-4 rounded-2xl transition-all duration-300 mb-1 ${selectedContact?.id === contact.id ? 'bg-white dark:bg-gray-800 shadow-md border-l-4 border-[#105F68]' : 'hover:bg-gray-100/50 dark:hover:bg-gray-800/30'}`}
                        >
                            <div className="relative">
                                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] flex items-center justify-center text-white font-bold text-lg shadow-sm">
                                    {contact.name[0]}
                                </div>
                                {contact.status === 'online' && (
                                    <div className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white dark:border-gray-900 shadow-sm" />
                                )}
                            </div>
                            <div className="flex-1 text-left min-w-0">
                                <div className="flex justify-between items-center mb-0.5">
                                    <h4 className="font-bold text-sm text-gray-900 dark:text-gray-100 truncate">{contact.name}</h4>
                                    {(contact.unread_count ?? 0) > 0 ? (
                                        <span className="min-w-5 h-5 px-1.5 rounded-full bg-[#105F68] text-white text-[10px] font-bold flex items-center justify-center">
                                            {contact.unread_count}
                                        </span>
                                    ) : contact.last_message_time ? (
                                        <span className="text-[10px] text-gray-400 font-medium">
                                            {new Date(contact.last_message_time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    ) : null}
                                </div>
                                <p className="text-xs text-gray-500 truncate dark:text-gray-400">{contact.last_message}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Chat Window */}
            <div className={`flex-1 flex flex-col bg-white dark:bg-gray-900 relative ${!selectedContact ? 'hidden md:flex' : 'flex'}`}>
                {selectedContact ? (
                    <>
                        {/* Chat Header */}
                        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-white/50 dark:bg-gray-900/50 backdrop-blur-md sticky top-0 z-10">
                            <div className="flex items-center gap-4">
                                <button className="md:hidden p-2 text-gray-500" onClick={() => setSelectedContact(null)}>
                                    <ChevronLeft className="w-6 h-6" />
                                </button>
                                <div className="w-10 h-10 rounded-xl bg-[#C8E6E2] flex items-center justify-center text-[#105F68] font-black shadow-sm">
                                    {selectedContact.name[0]}
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 dark:text-gray-100">{selectedContact.name}</h3>
                                    <p className={`text-[10px] font-bold uppercase tracking-widest ${selectedContact.status === 'online' ? 'text-green-500' : 'text-gray-400'}`}>{selectedContact.status}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setIsToolboxOpen(!isToolboxOpen)}
                                    className={`p-2.5 rounded-xl transition-all flex items-center gap-2 font-bold text-xs ${isToolboxOpen ? 'bg-[#105F68] text-white' : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                                >
                                    <Sparkles className="w-5 h-5" />
                                    Sign Tools
                                </button>
                            </div>
                        </div>

                        {/* Message Thread */}
                        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-6 bg-gray-50/20 dark:bg-transparent">
                            {threadMessages.map((msg) => (
                                <div key={msg.id} className={`flex ${msg.sender_id === sessionId ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[70%] group relative flex flex-col ${msg.sender_id === sessionId ? 'items-end' : 'items-start'}`}>
                                        <div className={`p-4 rounded-[24px] text-sm font-medium shadow-sm transition-all hover:shadow-md ${msg.sender_id === sessionId ? 'bg-[#105F68] text-white rounded-tr-none' : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-100 dark:border-gray-700 rounded-tl-none'}`}>
                                            {msg.content}
                                        </div>
                                        <p className="text-[10px] text-gray-400 mt-2 font-bold px-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {new Date(msg.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            <div ref={chatEndRef} />
                        </div>

                        {/* Chat Input */}
                        <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900">
                            <form onSubmit={handleSendMessage} className="flex items-center gap-4 bg-gray-50 dark:bg-gray-800 p-2 rounded-[24px] border border-gray-100 dark:border-gray-700 shadow-inner">
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder={selectedContact.id === 'official_bot' ? 'This account does not accept replies' : 'Type a message...'}
                                    maxLength={2000}
                                    disabled={selectedContact.id === 'official_bot'}
                                    className="flex-1 bg-transparent border-none outline-none py-3 px-2 text-sm font-medium text-gray-900 dark:text-gray-100"
                                />
                                <button type="submit" className="p-4 bg-gradient-to-br from-[#105F68] to-[#3A9295] text-white rounded-2xl shadow-xl hover:scale-105 transition-transform"><Send className="w-5 h-5" /></button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-12 space-y-6">
                        <div className="w-24 h-24 bg-gray-50 dark:bg-gray-800 rounded-full flex items-center justify-center text-5xl opacity-40 grayscale">💬</div>
                        <div>
                            <h3 className="text-2xl font-black text-gray-900 dark:text-gray-100 mb-2">Select a Conversation</h3>
                            <p className="text-gray-500 max-w-xs mx-auto">Click on a contact from the sidebar to chat over real-time WebSockets.</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Right Sidebar: Sign Toolbox */}
            {isToolboxOpen && (
                <div className="w-80 hidden lg:block">
                    <SignToolbox onClose={() => setIsToolboxOpen(false)} />
                </div>
            )}
        </div>
    );
}
