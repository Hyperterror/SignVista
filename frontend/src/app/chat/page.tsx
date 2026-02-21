"use client";

import { useState, useEffect, useRef } from 'react';
import {
    Search,
    MoreVertical,
    Send,
    Plus,
    Phone,
    Video,
    Info,
    Smile,
    Paperclip,
    ChevronLeft,
    Sparkles
} from 'lucide-react';
import { api } from '../utils/api';
import SignToolbox from '../components/chat/SignToolbox';
import { toast } from 'sonner';
import gsap from 'gsap';

export default function ChatPage() {
    const [contacts, setContacts] = useState<any[]>([]);
    const [selectedContact, setSelectedContact] = useState<any>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [isToolboxOpen, setIsToolboxOpen] = useState(true);
    const [isLoading, setIsLoading] = useState(true);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const ws = useRef<WebSocket | null>(null);
    const sessionId = api.getSessionId(); // My user ID

    useEffect(() => {
        const loadContacts = async () => {
            try {
                const data = await api.get('/chat/contacts');
                setContacts(data);
                if (data.length > 0) setSelectedContact(data[0]);
            } catch (error) {
                toast.error('Failed to load contacts');
            } finally {
                setIsLoading(false);
            }
        };
        loadContacts();

        if (sessionId && !ws.current) {
            // Initialize WebSocket connection
            const socket = new WebSocket(`ws://localhost:8001/api/chat/ws/${sessionId}`);
            ws.current = socket;

            socket.onopen = () => console.log("Chat WebSocket Connected");
            socket.onmessage = (event) => {
                try {
                    const incomingMsg = JSON.parse(event.data);
                    setMessages((prev) => [...prev, incomingMsg]);
                } catch (e) {
                    console.error("Failed to parse WS message", e);
                }
            };
            socket.onerror = (err) => {
                console.error("WS Error", err);
                toast.error("WebSocket connection error");
            };
            socket.onclose = () => {
                console.log("Chat WebSocket Disconnected");
                ws.current = null;
            };
        }

        // Cleanup socket on unmount
        return () => {
            if (ws.current) {
                const socket = ws.current;
                if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
                    socket.close();
                }
                ws.current = null;
            }
        };
    }, [sessionId]);

    useEffect(() => {
        if (selectedContact) {
            // For now, clear history and rely strictly on real-time broadcasts
            // In a production app, we'd fetch SQLite history here.
            setMessages([]);
        }
    }, [selectedContact]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedContact || !ws.current) return;

        const msgContent = newMessage;
        setNewMessage('');

        const payload = {
            receiver_id: selectedContact.id,
            content: msgContent,
            type: 'text'
        };

        // Send directly via WebSocket instead of HTTP POST
        ws.current.send(JSON.stringify(payload));
    };

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
                        <button className="p-2 bg-[#105F68] text-white rounded-xl shadow-lg hover:scale-110 transition-transform">
                            <Plus className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-[#105F68] transition-colors" />
                        <input
                            type="text"
                            placeholder="Search chats..."
                            className="w-full pl-11 pr-4 py-3 rounded-2xl bg-white dark:bg-gray-800 border-none shadow-sm focus:ring-2 focus:ring-[#105F68]/10 transition-all text-sm font-medium"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                    {contacts.map((contact) => (
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
                                    <span className="text-[10px] text-gray-400 font-medium">Live</span>
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
                                    <p className="text-[10px] font-bold text-green-500 uppercase tracking-widest">{selectedContact.status}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button className="p-2.5 text-gray-400 hover:text-[#105F68] hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all">
                                    <Phone className="w-5 h-5" />
                                </button>
                                <button className="p-2.5 text-gray-400 hover:text-[#105F68] hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-all">
                                    <Video className="w-5 h-5" />
                                </button>
                                <div className="w-px h-8 bg-gray-100 dark:border-gray-800 mx-2" />
                                <button
                                    onClick={() => setIsToolboxOpen(!isToolboxOpen)}
                                    className={`p-2.5 rounded-xl transition-all flex items-center gap-2 font-bold text-xs ${isToolboxOpen ? 'bg-[#105F68] text-white' : 'text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                                >
                                    <Sparkles className="w-5 h-5" />
                                    Sign Tools
                                </button>
                                <button className="p-2.5 text-gray-400 hover:text-gray-900 rounded-xl transition-all">
                                    <MoreVertical className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Message Thread */}
                        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-6 bg-gray-50/20 dark:bg-transparent">
                            {threadMessages.map((msg, i) => (
                                <div key={i} className={`flex ${msg.sender_id === sessionId ? 'justify-end' : 'justify-start'}`}>
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
                                <button type="button" className="p-3 text-gray-400 hover:text-[#105F68] transition-colors"><Smile className="w-6 h-6" /></button>
                                <button type="button" className="p-3 text-gray-400 hover:text-[#105F68] transition-colors"><Paperclip className="w-6 h-6" /></button>
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder="Type a message to send over live WebSocket..."
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
