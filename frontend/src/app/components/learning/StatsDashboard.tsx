"use client";

import { motion } from "framer-motion";
import { BookOpen, Hand, BarChart3, Gamepad2 } from "lucide-react";
import { useEffect, useState } from "react";

// Antigravity ease
const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];

const CircularProgress = ({ value, color, delay = 0 }: { value: number; color: string; delay?: number }) => {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const timer = setTimeout(() => setProgress(value), delay * 1000 + 500);
        return () => clearTimeout(timer);
    }, [value, delay]);

    const radius = 16;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (progress / 100) * circumference;

    return (
        <div className="relative w-10 h-10 flex items-center justify-center">
            <svg className="w-10 h-10 transform -rotate-90">
                <circle
                    className="stroke-[#3A9295]/30"
                    strokeWidth="3"
                    fill="transparent"
                    r={radius}
                    cx="20"
                    cy="20"
                />
                <motion.circle
                    className="stroke-current"
                    style={{ color }}
                    strokeWidth="3"
                    strokeLinecap="round"
                    fill="transparent"
                    r={radius}
                    cx="20"
                    cy="20"
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1.5, ease: AG_EASE }}
                    strokeDasharray={circumference}
                />
            </svg>
            <span className="absolute text-[10px] font-bold text-[#C8E6E2]">
                {value >= 0 ? "+" : ""}{value}%
            </span>
        </div>
    );
};

const StatCard = ({
    icon: Icon,
    iconColor,
    progressValue,
    progressColor,
    mainStat,
    subStat,
    subStatColor,
    label,
    delayIdx,
    floatDuration,
    isExtraBouncy = false,
    isWarm = false,
    accentColor,
}: {
    icon: any;
    iconColor: string;
    progressValue: number;
    progressColor: string;
    mainStat: string;
    subStat: string;
    subStatColor: string;
    label: string;
    delayIdx: number;
    floatDuration: number;
    isExtraBouncy?: boolean;
    isWarm?: boolean;
    accentColor: string;
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: delayIdx * 0.1, ease: AG_EASE }}
            className="relative w-full h-full"
        >
            <motion.div
                animate={{ y: [0, isExtraBouncy ? -12 : -8, 0] }}
                transition={{
                    duration: floatDuration,
                    repeat: Infinity,
                    ease: "easeInOut",
                }}
                whileHover={{
                    y: -10,
                    boxShadow: isWarm
                        ? "0 16px 40px rgba(239, 68, 68, 0.15)"
                        : "0 16px 40px rgba(16, 95, 104, 0.25)",
                    borderColor: isWarm ? "rgba(239, 68, 68, 0.4)" : "#63C1BB",
                    transition: { duration: 0.3, ease: AG_EASE },
                }}
                className={`
                    w-full h-full p-5 flex flex-col justify-between cursor-pointer transition-all duration-300 relative overflow-hidden
                    bg-white dark:bg-gray-800/80 backdrop-blur-md 
                    border border-gray-100 dark:border-gray-700 rounded-[20px]
                `}
            >
                {/* Vertical Accent Bar (Light Mode only) */}
                <div className="absolute right-0 top-0 bottom-0 w-1.5 h-full opacity-100 dark:opacity-0 transition-opacity" style={{ backgroundColor: accentColor }}>
                    <div className="absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-10 rounded-l-full" style={{ backgroundColor: accentColor }}></div>
                </div>

                <div className="flex justify-between items-start mb-4 relative z-10">
                    <div className="p-2 rounded-xl bg-gray-50 dark:bg-gray-900/50">
                        <Icon className="w-6 h-6" style={{ color: iconColor }} />
                    </div>
                    <CircularProgress value={progressValue} color={progressColor} delay={delayIdx * 0.1} />
                </div>

                <div className="relative z-10">
                    <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">{mainStat}</span>
                        <span className="text-sm font-medium" style={{ color: subStatColor }}>
                            {subStat}
                        </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-bold">
                        {label}
                    </p>
                </div>
            </motion.div>
        </motion.div>
    );
};

interface StatsProps {
    totalWords: number;
    practiced: number;
    proficiency: number;
    streak: number;
}

export function StatsDashboard({ totalWords, practiced, proficiency, streak }: StatsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full mb-12">
            <StatCard
                icon={BookOpen}
                iconColor="#4F46E5"
                progressValue={100}
                progressColor="#4F46E5"
                mainStat={totalWords.toString()}
                subStat=""
                subStatColor="#4F46E5"
                label="Total signs in dictionary"
                delayIdx={0}
                floatDuration={2.8}
                accentColor="#4F46E5"
            />

            <StatCard
                icon={Hand}
                iconColor="#0EA5E9"
                progressValue={practiced > 0 ? Math.round((practiced / totalWords) * 100) : 0}
                progressColor="#0EA5E9"
                mainStat={practiced.toString()}
                subStat=""
                subStatColor="#0EA5E9"
                label="Signs Practiced"
                delayIdx={1}
                floatDuration={3.2}
                accentColor="#0EA5E9"
            />

            <StatCard
                icon={BarChart3}
                iconColor="#9333EA"
                progressValue={proficiency}
                progressColor="#9333EA"
                mainStat={`${proficiency}%`}
                subStat=""
                subStatColor="#9333EA"
                label="Overall ISL proficiency score"
                delayIdx={2}
                floatDuration={3.6}
                isWarm={false}
                accentColor="#9333EA"
            />

            <StatCard
                icon={Gamepad2}
                iconColor="#10B981"
                progressValue={streak * 10}
                progressColor="#10B981"
                mainStat={streak.toString()}
                subStat=" days"
                subStatColor="#10B981"
                label="Current Learning Streak"
                delayIdx={3}
                floatDuration={4.0}
                isExtraBouncy={true}
                accentColor="#10B981"
            />
        </div>
    );
}

