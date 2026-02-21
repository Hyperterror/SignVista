"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { Users, MessageCircle, Heart, Share2, Plus, Search, Filter, Globe, ShieldCheck, X, Send } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'sonner';

export default function CommunityPage() {
    const [activeTab, setActiveTab] = useState('feed');
    const [posts, setPosts] = useState<any[]>([]);
    const [activeUsers, setActiveUsers] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isPostModalOpen, setIsPostModalOpen] = useState(false);
    const [newPostContent, setNewPostContent] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchData = async () => {
        try {
            setIsLoading(true);
            const [feedData, usersData] = await Promise.all([
                api.getCommunityFeed(),
                api.getActiveUsers()
            ]);
            setPosts(feedData.posts);
            setActiveUsers(usersData.users);
        } catch (error) {
            console.error(error);
            toast.error('Failed to sync with community');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        // Polling for active users every 30s
        const interval = setInterval(() => {
            api.getActiveUsers().then(data => setActiveUsers(data.users)).catch(() => { });
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (!isLoading && posts.length > 0) {
            const animateCards = () => {
                if (document.querySelector('.community-card')) {
                    gsap.fromTo('.community-card',
                        { scale: 0.95, opacity: 0, y: 20 },
                        { scale: 1, opacity: 1, y: 0, duration: 0.5, stagger: 0.1, ease: 'power2.out' }
                    );
                }
            };
            requestAnimationFrame(animateCards);
        }
    }, [isLoading, posts]);

    const handleCreatePost = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newPostContent.trim()) return;

        try {
            setIsSubmitting(true);
            await api.createPost(newPostContent);
            toast.success('Post shared with the community!');
            setNewPostContent('');
            setIsPostModalOpen(false);
            fetchData(); // Refresh feed
        } catch (error) {
            toast.error('Failed to share post');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleLike = async (postId: string) => {
        try {
            const result = await api.likePost(postId);
            if (result.status === 'ok') {
                setPosts(prev => prev.map(p =>
                    p.id === postId ? { ...p, likes: result.likes } : p
                ));
            }
        } catch (error) {
            toast.error('Could not process like');
        }
    };

    const formatTime = (timestamp: number) => {
        const diff = Date.now() / 1000 - timestamp;
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    };

    return (
        <div className="min-h-screen p-6 md:p-12 bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-black text-[#105F68] dark:text-[#63C1BB]">Community Hub</h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">Connect, share, and learn with signers across India</p>
                    </div>
                    <button
                        onClick={() => setIsPostModalOpen(true)}
                        className="px-6 py-4 bg-gradient-to-br from-[#105F68] to-[#3A9295] text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all flex items-center gap-2 hover:scale-[1.02] active:scale-95"
                    >
                        <Plus className="w-5 h-5" /> New Post
                    </button>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Main Feed */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex gap-4 p-1.5 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                            <button
                                onClick={() => setActiveTab('feed')}
                                className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'feed' ? 'bg-[#105F68] text-white shadow-md' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            >
                                Live Feed
                            </button>
                            <button
                                onClick={() => setActiveTab('explore')}
                                className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'explore' ? 'bg-[#105F68] text-white shadow-md' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            >
                                Explore Groups
                            </button>
                        </div>

                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-20 opacity-50">
                                <div className="w-12 h-12 border-4 border-[#105F68] border-t-transparent rounded-full animate-spin mb-4" />
                                <p className="font-bold text-[#105F68]">Syncing community feed...</p>
                            </div>
                        ) : posts.length > 0 ? (
                            posts.map((item) => (
                                <div key={item.id} className="community-card bg-white dark:bg-gray-900 rounded-3xl p-8 shadow-xl border border-gray-100 dark:border-gray-800 group transition-all hover:border-[#105F68]/30">
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] flex items-center justify-center text-white text-xl font-black shadow-lg transform group-hover:rotate-2 transition-transform">
                                            {item.avatar_initials}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{item.user_name}</h3>
                                                {item.is_official && (
                                                    <span title="Official SignVista Team">
                                                        <ShieldCheck className="w-5 h-5 text-[#105F68]" />
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm font-medium text-gray-400">{formatTime(item.timestamp)}</p>
                                        </div>
                                    </div>

                                    <p className="text-xl text-gray-700 dark:text-gray-200 mb-6 leading-relaxed font-medium">
                                        {item.content}
                                    </p>

                                    <div className="flex flex-wrap gap-2 mb-6">
                                        {item.tags?.map((tag: string) => (
                                            <span key={tag} className="text-sm font-bold text-[#105F68] dark:text-[#63C1BB] hover:underline cursor-pointer">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>

                                    {item.achievement_text && (
                                        <div className="mb-6 p-5 bg-[#C8E6E2]/20 dark:bg-[#105F68]/10 rounded-2xl flex items-center gap-4 border border-[#C8E6E2]/50 dark:border-[#105F68]/30">
                                            <div className="w-10 h-10 rounded-xl bg-white dark:bg-gray-800 flex items-center justify-center shadow-sm">
                                                <Globe className="w-6 h-6 text-[#105F68]" />
                                            </div>
                                            <span className="text-base font-black text-[#105F68] dark:text-[#63C1BB]">{item.achievement_text}</span>
                                        </div>
                                    )}

                                    <div className="flex items-center gap-8 pt-6 border-t border-gray-50 dark:border-gray-800">
                                        <button
                                            onClick={() => handleLike(item.id)}
                                            className="flex items-center gap-3 text-gray-400 hover:text-pink-500 transition-all font-bold group/like"
                                        >
                                            <Heart className={`w-6 h-6 transition-transform group-active/like:scale-150 ${item.likes > 0 ? 'fill-pink-500 text-pink-500' : ''}`} />
                                            <span>{item.likes}</span>
                                        </button>
                                        <button className="flex items-center gap-3 text-gray-400 hover:text-[#105F68] transition-all font-bold">
                                            <MessageCircle className="w-6 h-6" />
                                            <span>{item.comments_count}</span>
                                        </button>
                                        <button className="ml-auto text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                                            <Share2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="bg-white dark:bg-gray-800 rounded-3xl p-12 text-center border-2 border-dashed border-gray-200 dark:border-gray-700">
                                <p className="text-xl font-bold text-gray-400">The community is quiet... be the first to post!</p>
                            </div>
                        )}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-8">
                        {/* Users Box */}
                        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 shadow-xl border border-gray-100 dark:border-gray-800">
                            <h3 className="text-xl font-bold mb-8 flex items-center gap-3 text-gray-900 dark:text-gray-100">
                                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-xl">
                                    <Users className="w-5 h-5 text-green-600" />
                                </div>
                                Active Now
                            </h3>

                            <div className="space-y-6">
                                {activeUsers.map((user, i) => (
                                    <div key={i} className="flex items-center gap-4 group cursor-pointer hover:translate-x-1 transition-transform">
                                        <div className="relative">
                                            <div className="w-12 h-12 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center font-bold text-gray-500 group-hover:bg-[#105F68] group-hover:text-white transition-colors uppercase">
                                                {user.initials}
                                            </div>
                                            {user.is_online && (
                                                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-4 border-white dark:border-gray-900" />
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-800 dark:text-gray-200">{user.name}</p>
                                            <p className="text-xs font-bold text-green-500 uppercase tracking-widest">Online</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Trending */}
                        <div className="bg-gradient-to-br from-[#105F68] to-[#3A9295] rounded-3xl p-8 text-white shadow-xl relative overflow-hidden group">
                            <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                                <Globe className="w-32 h-32" />
                            </div>
                            <h3 className="text-xl font-black mb-6 flex items-center gap-2">
                                Trending Tags
                            </h3>
                            <div className="flex flex-wrap gap-2 relative z-10">
                                {["#ISL_Daily", "#SignVista", "#LearnSign", "#DeafPride", "#IndiaSign"].map(tag => (
                                    <button key={tag} className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-sm font-bold transition-all hover:scale-105 active:scale-95">
                                        {tag}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* New Post Modal */}
            {isPostModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="bg-white dark:bg-gray-900 rounded-[40px] w-full max-w-xl p-8 shadow-2xl relative translate-y-0 scale-100 transition-all duration-300 border border-white/20">
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-2xl bg-[#105F68] flex items-center justify-center text-white">
                                    <Plus className="w-6 h-6" />
                                </div>
                                <h2 className="text-3xl font-black text-gray-900 dark:text-gray-100">Create Post</h2>
                            </div>
                            <button
                                onClick={() => setIsPostModalOpen(false)}
                                className="p-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                            >
                                <X className="w-6 h-6 text-gray-400" />
                            </button>
                        </div>

                        <form onSubmit={handleCreatePost} className="space-y-6">
                            <textarea
                                value={newPostContent}
                                onChange={(e) => setNewPostContent(e.target.value)}
                                placeholder="What's your Sign Language update today?"
                                className="w-full h-40 p-6 bg-gray-50 dark:bg-gray-800/50 rounded-3xl border border-gray-100 dark:border-gray-700 outline-none focus:border-[#105F68] transition-all resize-none text-lg font-medium dark:text-white"
                                autoFocus
                            />

                            <div className="flex gap-4">
                                <button
                                    type="button"
                                    onClick={() => setIsPostModalOpen(false)}
                                    className="flex-1 h-16 rounded-2xl font-black text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all uppercase tracking-widest text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting || !newPostContent.trim()}
                                    className="flex-[2] h-16 rounded-2xl bg-[#105F68] text-white font-black shadow-lg hover:shadow-2xl transition-all flex items-center justify-center gap-3 disabled:opacity-50 uppercase tracking-widest text-sm"
                                >
                                    {isSubmitting ? 'Sharing...' : (
                                        <>
                                            Post Hub <Send className="w-4 h-4" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
