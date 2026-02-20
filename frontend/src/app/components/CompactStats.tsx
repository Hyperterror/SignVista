"use client";

import { Flame, Target, Star, TrendingUp } from 'lucide-react';
import { Progress } from './ui/progress';

interface DashboardData {
    xp_info: {
        current_xp: number;
        level: number;
        next_level_xp: number;
        progress_percent: number;
    };
    overall_proficiency: number;
    words_practiced: number;
    current_streak: number;
}

export function CompactStats({ data }: { data: DashboardData }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
            {/* XP progress */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Star className="w-5 h-5 text-yellow-500 fill-current" />
                        <span className="font-bold text-sm">Level {data.xp_info.level}</span>
                    </div>
                    <span className="text-[10px] bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full font-bold">XP PROGRESS</span>
                </div>
                <div>
                    <div className="flex justify-between text-[10px] mb-1 font-bold opacity-60">
                        <span>{data.xp_info.current_xp} XP</span>
                        <span>{data.xp_info.next_level_xp} XP</span>
                    </div>
                    <Progress value={data.xp_info.progress_percent} className="h-2 bg-gray-100 dark:bg-gray-700" />
                </div>
            </div>

            {/* Streak */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-orange-50 dark:bg-orange-950/30 flex items-center justify-center">
                    <Flame className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                    <div className="text-2xl font-black text-gray-900 dark:text-gray-100 leading-none">{data.current_streak}</div>
                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-1">Day Streak</div>
                </div>
            </div>

            {/* Proficiency */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-green-50 dark:bg-green-950/30 flex items-center justify-center">
                    <Target className="w-6 h-6 text-green-600" />
                </div>
                <div>
                    <div className="text-2xl font-black text-gray-900 dark:text-gray-100 leading-none">{Math.round(data.overall_proficiency * 100)}%</div>
                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-1">Proficiency</div>
                </div>
            </div>
        </div>
    );
}
