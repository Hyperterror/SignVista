"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { Users, MessageCircle, Heart, Share2, Plus, Search, Filter, Globe, ShieldCheck } from 'lucide-react';

export default function CommunityPage() {
    const [activeTab, setActiveTab] = useState('feed');

    useEffect(() => {
        gsap.fromTo('.community-card',
            { scale: 0.95, opacity: 0 },
            { scale: 1, opacity: 1, duration: 0.5, stagger: 0.1, ease: 'power2.out' }
        );
    }, []);

    const feedItems = [
        {
            id: 1,
            user: "Ishaan Sharma",
            avatar: "IS",
            time: "2h ago",
            content: "Just mastered the 'Welcome' sign in ISL! The AI feedback was super helpful in correcting my hand orientation. 🤟",
            likes: 24,
            comments: 5,
            achievement: "Mastered: Welcome"
        },
        {
            id: 2,
            user: "Priya Patel",
            avatar: "PP",
            time: "5h ago",
            content: "Anyone interested in a group practice session this weekend? Focusing on 'Common Phrases' category. Let's learn together!",
            likes: 12,
            comments: 8,
            tags: ["#PracticeSession", "#ISL"]
        },
        {
            id: 3,
            user: "SignVista Team",
            avatar: "SV",
            time: "1d ago",
            content: "New update: Added 50+ medical signs to the dictionary. Stay informed, stay safe! 🏥",
            likes: 156,
            comments: 12,
            official: true
        }
    ];

    return (
        <div className="min-h-screen p-6 md:p-12 bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-black text-[#105F68] dark:text-[#63C1BB]">Community Hub</h1>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">Connect, share, and learn with signers across India</p>
                    </div>
                    <button className="px-6 py-3 bg-[#105F68] text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all flex items-center gap-2">
                        <Plus className="w-5 h-5" /> New Post
                    </button>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Main Feed */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="flex gap-4 p-1.5 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                            <button
                                onClick={() => setActiveTab('feed')}
                                className={`flex-1 py-2 rounded-xl font-bold text-sm transition-all ${activeTab === 'feed' ? 'bg-[#105F68] text-white' : 'text-gray-500'}`}
                            >
                                Feed
                            </button>
                            <button
                                onClick={() => setActiveTab('explore')}
                                className={`flex-1 py-2 rounded-xl font-bold text-sm transition-all ${activeTab === 'explore' ? 'bg-[#105F68] text-white' : 'text-gray-500'}`}
                            >
                                Explore Groups
                            </button>
                        </div>

                        {feedItems.map((item) => (
                            <div key={item.id} className="community-card bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-700 group">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] flex items-center justify-center text-white font-black shadow-lg">
                                        {item.avatar}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-bold text-gray-900 dark:text-gray-100">{item.user}</h3>
                                            {item.official && <ShieldCheck className="w-4 h-4 text-[#105F68]" />}
                                        </div>
                                        <p className="text-xs text-gray-500">{item.time}</p>
                                    </div>
                                </div>

                                <p className="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                                    {item.content}
                                </p>

                                {item.achievement && (
                                    <div className="mb-4 p-4 bg-[#C8E6E2]/30 rounded-2xl flex items-center gap-3 border border-[#C8E6E2]">
                                        <Globe className="w-5 h-5 text-[#105F68]" />
                                        <span className="text-sm font-bold text-[#105F68]">{item.achievement}</span>
                                    </div>
                                )}

                                <div className="flex items-center gap-6 pt-4 border-t border-gray-50 dark:border-gray-700">
                                    <button className="flex items-center gap-2 text-gray-500 hover:text-pink-500 transition-colors">
                                        <Heart className="w-5 h-5" />
                                        <span className="text-xs font-bold">{item.likes}</span>
                                    </button>
                                    <button className="flex items-center gap-2 text-gray-500 hover:text-blue-500 transition-colors">
                                        <MessageCircle className="w-5 h-5" />
                                        <span className="text-xs font-bold">{item.comments}</span>
                                    </button>
                                    <button className="ml-auto flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors">
                                        <Share2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-700">
                            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                                <Search className="w-5 h-5 text-[#105F68]" /> Find Friends
                            </h3>
                            <div className="relative mb-6">
                                <input
                                    type="text"
                                    placeholder="Search community..."
                                    className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 outline-none focus:border-[#105F68] transition-all"
                                />
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            </div>

                            <div className="space-y-4">
                                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Active Now</h4>
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="flex items-center gap-3">
                                        <div className="relative">
                                            <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700" />
                                            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-800" />
                                        </div>
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">User_{i * 42}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-gradient-to-br from-[#105F68] to-[#3A9295] rounded-3xl p-8 text-white shadow-xl">
                            <h3 className="text-xl font-bold mb-4">Trending Tags</h3>
                            <div className="flex flex-wrap gap-2">
                                {["#ISL_Daily", "#SignVista", "#LearnSign", "#DeafPride", "#IndiaSign"].map(tag => (
                                    <span key={tag} className="px-3 py-1 bg-white/10 rounded-lg text-xs font-medium hover:bg-white/20 cursor-pointer transition-all">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
