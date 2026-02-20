"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import {
    User,
    Award,
    History,
    Star,
    Calendar,
    TrendingUp,
    ChevronRight,
    Settings,
    Mail,
    Phone,
    Globe,
    Trophy
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface Achievement {
    id: string;
    name: string;
    description: string;
    icon: string;
    unlocked: boolean;
    unlocked_at: number | null;
    category: string;
}

interface ActivityEvent {
    type: string;
    title: string;
    description: string;
    xp_earned: number;
    timestamp: number;
}

export default function ProfilePage() {
    const [profile, setProfile] = useState<any>(null);
    const [dashboard, setDashboard] = useState<any>(null);
    const [achievements, setAchievements] = useState<Achievement[]>([]);
    const [history, setHistory] = useState<ActivityEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'achievements' | 'history'>('achievements');
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Form states
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        phone: ''
    });

    const fetchData = async () => {
        try {
            const [achData, histData, profData, dashData] = await Promise.all([
                api.getAchievements(),
                api.getHistory(),
                api.getProfile().catch(() => null), // Profile might not exist yet
                api.getDashboard()
            ]);

            setAchievements(achData.achievements);
            setHistory(histData.activities || []);
            setProfile(profData);
            setDashboard(dashData);

            if (profData) {
                setFormData({
                    name: profData.name,
                    email: profData.email,
                    phone: profData.phone || ''
                });
            }
        } catch (error) {
            console.error(error);
            toast.error('Failed to load profile data');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (!isLoading) {
            gsap.fromTo('.profile-header', { y: -50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out' });
        }
    }, [isLoading]);

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setIsSaving(true);
            await api.updateProfile(formData.name, formData.email, formData.phone);
            toast.success('Persona updated successfully!');
            setIsEditModalOpen(false);
            await fetchData(); // Refresh data
        } catch (error) {
            toast.error('Failed to update persona');
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6 bg-white dark:bg-gray-900">
                <div className="w-12 h-12 border-4 border-[#105F68] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const userName = profile?.name || 'New Signer';
    const initials = userName.split(' ').map((n: string) => n[0]).join('').toUpperCase();

    return (
        <div className="min-h-screen p-6 md:p-12 bg-[#F8FAFA] dark:bg-gray-900 transition-colors duration-500">
            <div className="max-w-6xl mx-auto">
                {/* Profile Header */}
                <div className="profile-header bg-white dark:bg-gray-800 rounded-[32px] p-8 md:p-12 shadow-2xl border border-gray-100 dark:border-gray-700 mb-12 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#C8E6E2]/20 rounded-full blur-3xl -mr-32 -mt-32" />

                    <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
                        <div className="relative">
                            <div className="w-32 h-32 rounded-3xl bg-gradient-to-br from-[#105F68] to-[#3A9295] flex items-center justify-center text-white text-4xl font-black shadow-xl transform rotate-3">
                                {initials}
                            </div>
                            <div className="absolute -bottom-2 -right-2 w-10 h-10 bg-yellow-400 rounded-2xl flex items-center justify-center border-4 border-white dark:border-gray-800 shadow-lg">
                                <Star className="w-5 h-5 text-yellow-900 fill-current" />
                            </div>
                        </div>

                        <div className="flex-1 text-center md:text-left">
                            <h1 className="text-4xl font-black text-gray-900 dark:text-gray-100 mb-2 tracking-tight">{userName}</h1>
                            <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm text-gray-500 dark:text-gray-400">
                                <span className="flex items-center gap-1.5"><Mail className="w-4 h-4" /> {profile?.email || 'not set'}</span>
                                {profile?.phone && <span className="flex items-center gap-1.5"><Phone className="w-4 h-4" /> {profile.phone}</span>}
                                <span className="flex items-center gap-1.5"><Globe className="w-4 h-4" /> {profile?.preferred_language === 'hi' ? 'Hindi' : 'English'}</span>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button className="p-3 bg-gray-50 dark:bg-gray-700 rounded-2xl border border-gray-100 dark:border-gray-600 hover:bg-gray-100 transition-colors shadow-sm">
                                <Settings className="w-6 h-6 text-gray-400" />
                            </button>
                            <button
                                onClick={() => setIsEditModalOpen(true)}
                                className="px-6 py-3 bg-[#105F68] text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all hover:scale-105"
                            >
                                Edit Persona
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12 pt-8 border-t border-gray-100 dark:border-gray-700">
                        <div className="text-center">
                            <p className="text-2xl font-black text-[#105F68] dark:text-[#63C1BB]">Level {dashboard?.xp_info?.level || 1}</p>
                            <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Signer Rank</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-black text-[#105F68] dark:text-[#63C1BB]">{achievements.filter(a => a.unlocked).length}</p>
                            <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Badges</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-black text-[#105F68] dark:text-[#63C1BB]">{history.length}</p>
                            <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Activities</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-black text-[#105F68] dark:text-[#63C1BB]">{Math.round(dashboard?.xp_info?.current_xp || 0)}</p>
                            <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Total XP</p>
                        </div>
                    </div>
                </div>

                {/* Content Section */}
                <div className="space-y-8">
                    <div className="flex p-1.5 bg-gray-100 dark:bg-gray-800 rounded-2xl w-full max-w-md mx-auto md:mx-0 shadow-inner">
                        <button
                            onClick={() => setActiveTab('achievements')}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'achievements' ? 'bg-white dark:bg-gray-700 text-[#105F68] dark:text-[#63C1BB] shadow-md' : 'text-gray-500'}`}
                        >
                            <Award className="w-4 h-4" /> Badges
                        </button>
                        <button
                            onClick={() => setActiveTab('history')}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all ${activeTab === 'history' ? 'bg-white dark:bg-gray-700 text-[#105F68] dark:text-[#63C1BB] shadow-md' : 'text-gray-500'}`}
                        >
                            <History className="w-4 h-4" /> Activity Feed
                        </button>
                    </div>

                    <div className="min-h-[400px]">
                        {activeTab === 'achievements' ? (
                            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                {achievements.map((ach) => (
                                    <div
                                        key={ach.id}
                                        className={`p-6 rounded-3xl border-2 transition-all duration-300 ${ach.unlocked ? 'bg-white dark:bg-gray-800 border-[#C8E6E2] shadow-xl hover:scale-[1.02]' : 'bg-gray-50 dark:bg-gray-900 border-gray-100 dark:border-gray-800 opacity-60 grayscale'}`}
                                    >
                                        <div className="flex items-start justify-between mb-4">
                                            <div className="w-16 h-16 rounded-2xl bg-[#C8E6E2]/30 flex items-center justify-center text-3xl">
                                                {ach.icon}
                                            </div>
                                            {ach.unlocked && <Trophy className="w-6 h-6 text-yellow-500" />}
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">{ach.name}</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-4">{ach.description}</p>
                                        {ach.unlocked && ach.unlocked_at && (
                                            <p className="text-[10px] font-bold text-[#105F68] dark:text-[#63C1BB] uppercase tracking-tighter">
                                                Unlocked on {new Date(ach.unlocked_at * 1000).toLocaleDateString()}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl border border-gray-100 dark:border-gray-700 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-gray-100 before:to-transparent dark:before:from-gray-700">
                                    {history.map((event, i) => (
                                        <div key={i} className="relative flex gap-8">
                                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white dark:bg-gray-800 border-2 border-[#105F68] z-10 shadow-lg">
                                                {event.type === 'learn_attempt' ? '📖' : event.type === 'game_completed' ? '🎮' : '🏆'}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-start justify-between mb-1">
                                                    <h4 className="font-bold text-gray-900 dark:text-gray-100">{event.title}</h4>
                                                    <span className="text-xs font-bold text-[#105F68] dark:text-[#63C1BB]">+{event.xp_earned} XP</span>
                                                </div>
                                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{event.description}</p>
                                                <div className="flex items-center gap-2 text-[10px] text-gray-400 uppercase tracking-widest font-bold">
                                                    <Calendar className="w-3 h-3" />
                                                    {new Date(event.timestamp * 1000).toLocaleString()}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {history.length === 0 && (
                                        <div className="text-center py-12">
                                            <p className="text-gray-400">No activity yet. Start your ISL journey!</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Edit Profile Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/5backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="bg-white dark:bg-gray-900 rounded-[40px] w-full max-w-lg p-10 shadow-2xl border border-gray-100 dark:border-gray-800 relative translate-y-0 scale-100 transition-all duration-300">
                        <h2 className="text-3xl font-black text-gray-900 dark:text-gray-100 mb-2">Edit Persona</h2>
                        <p className="text-gray-500 dark:text-gray-400 mb-8 font-medium">Update your digital identity on SignVista.</p>

                        <form onSubmit={handleUpdateProfile} className="space-y-6">
                            <div>
                                <label className="block text-xs font-black uppercase tracking-widest text-[#105F68] dark:text-[#63C1BB] mb-2">Full Name</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full h-14 px-6 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 focus:outline-none focus:ring-4 focus:ring-[#105F68]/10 text-gray-900 dark:text-gray-100 font-bold transition-all"
                                    placeholder="e.g. Ujjwal Kumar"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-black uppercase tracking-widest text-[#105F68] dark:text-[#63C1BB] mb-2">Email Address</label>
                                <input
                                    type="email"
                                    required
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full h-14 px-6 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 focus:outline-none focus:ring-4 focus:ring-[#105F68]/10 text-gray-900 dark:text-gray-100 font-bold transition-all"
                                    placeholder="e.g. hello@signbridge.ai"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-black uppercase tracking-widest text-[#105F68] dark:text-[#63C1BB] mb-2">Phone (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.phone}
                                    onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                    className="w-full h-14 px-6 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 focus:outline-none focus:ring-4 focus:ring-[#105F68]/10 text-gray-900 dark:text-gray-100 font-bold transition-all"
                                    placeholder="e.g. +91 98765 43210"
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsEditModalOpen(false)}
                                    className="flex-1 h-16 rounded-2xl font-black text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all uppercase tracking-widest text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSaving}
                                    className="flex-1 h-16 rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] text-white font-black shadow-lg hover:shadow-2xl transition-all hover:scale-[1.02] disabled:opacity-50 uppercase tracking-widest text-sm"
                                >
                                    {isSaving ? 'Saving...' : 'Save Meta'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
