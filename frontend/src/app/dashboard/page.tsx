"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import {
    Trophy,
    Flame,
    Target,
    Star,
    Activity,
    Award,
    ChevronRight,
    TrendingUp,
    Brain,
    History
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';
import { Progress } from '../components/ui/progress';

interface DashboardData {
    user_name: string;
    xp_info: {
        current_xp: number;
        level: number;
        next_level_xp: number;
        progress_percent: number;
    };
    overall_proficiency: number;
    words_practiced: number;
    words_mastered: number;
    current_streak: number;
    recent_activity: any[];
    unlocked_achievements_count: number;
    total_achievements: number;
    best_game_score: number;
    suggested_next_words: string[];
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                setIsLoading(true);
                const dashboardData = await api.getDashboard();
                setData(dashboardData);
            } catch (error) {
                toast.error('Failed to load dashboard data');
            } finally {
                setIsLoading(false);
            }
        };

        fetchDashboard();
    }, []);

    useEffect(() => {
        if (!isLoading && data) {
            gsap.fromTo(
                '.dashboard-card',
                { y: 30, opacity: 0 },
                { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'power3.out', delay: 0.2 }
            );
        }
    }, [isLoading, data]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-white dark:bg-gray-900">
                <div className="w-16 h-16 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-gray-600 dark:text-gray-400 font-medium">Preparing your SignBridge dashboard...</p>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="min-h-screen p-6 md:p-12 bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
            <div className="max-w-7xl mx-auto">
                {/* Welcome Header */}
                <div className="mb-12">
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                        SignBridge Hub
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400">
                        Track your progress and master ISL step by step
                    </p>
                </div>

                {/* Top Tier Stats */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    <div className="dashboard-card bg-gradient-to-br from-violet-600 to-indigo-700 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden group">
                        <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                            <Star className="w-32 h-32" />
                        </div>
                        <div className="relative z-10">
                            <div className="flex items-center justify-between mb-4">
                                <Star className="w-10 h-10 text-yellow-400 fill-current" />
                                <span className="text-xs px-2 py-1 bg-white/20 rounded-full">XP Goal</span>
                            </div>
                            <div className="text-4xl font-bold mb-2">{data.xp_info.current_xp} XP</div>
                            <Progress value={data.xp_info.progress_percent} className="h-2 bg-white/20 mb-2" />
                            <div className="text-sm opacity-80">{data.xp_info.next_level_xp - data.xp_info.current_xp} XP to Level {data.xp_info.level + 1}</div>
                        </div>
                    </div>

                    <div className="dashboard-card bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-lg group">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                                <Flame className="w-6 h-6 text-orange-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{data.current_streak} Days</div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">Current Streak</div>
                            </div>
                        </div>
                        <div className="flex gap-1">
                            {[1, 2, 3, 4, 5, 6, 7].map(d => (
                                <div key={d} className={`h-2 flex-1 rounded-full ${d <= (data.current_streak % 7 || 7) ? 'bg-orange-500' : 'bg-gray-100 dark:bg-gray-700'}`} />
                            ))}
                        </div>
                    </div>

                    <div className="dashboard-card bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-lg">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                <Target className="w-6 h-6 text-green-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{Math.round(data.overall_proficiency * 100)}%</div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">Proficiency</div>
                            </div>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-green-500" /> {data.words_practiced} words practiced
                        </div>
                    </div>

                    <div className="dashboard-card bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-lg">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                                <Award className="w-6 h-6 text-yellow-600" />
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{data.unlocked_achievements_count}/{data.total_achievements}</div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">Achievements</div>
                            </div>
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Keep going!</div>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-12">
                    <div className="lg:col-span-2 space-y-8">
                        <div className="dashboard-card bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-lg">
                            <div className="flex items-center justify-between mb-8">
                                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                                    <History className="w-6 h-6 text-violet-600" /> Recent Activity
                                </h3>
                                <button className="text-sm text-violet-600 font-medium hover:underline">View All</button>
                            </div>

                            <div className="space-y-6">
                                {data.recent_activity && data.recent_activity.length > 0 ? data.recent_activity.map((activity, i) => (
                                    <div key={i} className="flex gap-4 items-start group">
                                        <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-gray-700 flex items-center justify-center group-hover:bg-violet-50 dark:group-hover:bg-violet-900/30 transition-colors">
                                            {activity.type === 'learn' ? '📖' : activity.type === 'game' ? '🎮' : '⭐'}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex justify-between mb-1">
                                                <span className="font-semibold text-gray-900 dark:text-gray-100">{activity.title}</span>
                                                <span className="text-xs text-gray-500">{activity.xp_earned} XP</span>
                                            </div>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">{activity.description}</p>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="text-center py-10">
                                        <p className="text-gray-500">No recent activity. Start learning today!</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="dashboard-card bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-gray-800 dark:to-violet-900/20 rounded-3xl p-8 border border-violet-100 dark:border-violet-900/30 shadow-lg">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Recommended for You</h3>
                                <Brain className="w-8 h-8 text-violet-600" />
                            </div>
                            <div className="grid sm:grid-cols-2 gap-4">
                                {data.suggested_next_words && data.suggested_next_words.map(word => (
                                    <div key={word} className="bg-white/80 dark:bg-gray-900/80 p-4 rounded-2xl flex items-center justify-between hover:bg-white dark:hover:bg-gray-800 transition-colors cursor-pointer group shadow-sm">
                                        <span className="font-bold text-gray-900 dark:text-gray-100">{word}</span>
                                        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-8">
                        <div className="dashboard-card bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-lg">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-2">
                                <Activity className="w-6 h-6 text-pink-500" /> Weekly Insights
                            </h3>
                            <div className="space-y-4">
                                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-2xl">
                                    <div className="text-sm text-gray-500 mb-1">Best Game Score</div>
                                    <div className="text-2xl font-bold text-violet-600">{data.best_game_score}</div>
                                </div>
                                <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-2xl">
                                    <div className="text-sm text-gray-500 mb-1">Learning Time</div>
                                    <div className="text-2xl font-bold text-violet-600">2.5h</div>
                                </div>
                            </div>
                        </div>

                        <div className="dashboard-card bg-gradient-to-br from-gray-900 to-black rounded-3xl p-8 text-white shadow-xl">
                            <h3 className="text-xl font-bold mb-4">Daily Challenge</h3>
                            <p className="text-sm opacity-80 mb-6">Practice 5 signs from the "Common" category to earn bonus XP!</p>
                            <button className="w-full py-3 bg-violet-600 text-white rounded-xl font-bold hover:bg-violet-700 transition-all shadow-lg">
                                Start Challenge
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
