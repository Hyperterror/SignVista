'use client';

import { motion } from 'framer-motion';

type Tab = 'dictionary' | 'practice' | 'matrix';

interface NavigationPillBarProps {
    activeTab: Tab;
    setActiveTab: (tab: Tab) => void;
}

const easeBounce: [number, number, number, number] = [0.34, 1.56, 0.64, 1];

export function NavigationPillBar({ activeTab, setActiveTab }: NavigationPillBarProps) {
    const tabs = [
        { id: 'dictionary', label: 'ISL Dictionary' },
        { id: 'practice', label: 'Practice Lessons' },
        { id: 'matrix', label: 'Proficiency Matrix' },
    ];

    return (
        <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: easeBounce, delay: 0.1 }}
            className="relative flex items-center justify-center w-3/4 max-w-4xl"
        >
            {/* Floating Levitation Shadow */}
            <div className="absolute -bottom-4 w-[90%] h-4 bg-black/20 blur-xl rounded-full mix-blend-multiply pointer-events-none" />

            {/* Main Pill Bar */}
            <div className="flex items-center w-full bg-[#63C1BB] rounded-full p-2 shadow-[0_15px_30px_rgba(16,95,104,0.3)]">
                {tabs.map((tab, index) => {
                    const isActive = activeTab === tab.id;

                    return (
                        <div key={tab.id} className="flex-1 flex items-center justify-center relative">
                            <motion.button
                                onClick={() => setActiveTab(tab.id as Tab)}
                                whileHover={{ translateY: -3 }}
                                transition={{ ease: easeBounce }}
                                className={`relative z-10 w-full py-3 text-sm md:text-base font-bold transition-all duration-300 ${isActive ? 'text-white drop-shadow-md' : 'text-[#344C3D] opacity-70 hover:opacity-100 hover:text-white'
                                    }`}
                            >
                                {tab.label}

                                {/* Active Underline Glow */}
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTabGlow"
                                        transition={{ ease: easeBounce, duration: 0.5 }}
                                        className="absolute -bottom-1 left-1/4 right-1/4 h-1 bg-[#9ED5D1] rounded-full shadow-[0_0_12px_#9ED5D1]"
                                    />
                                )}
                            </motion.button>

                            {/* Separator Line */}
                            {index < tabs.length - 1 && (
                                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-px h-1/2 bg-white/40" />
                            )}
                        </div>
                    );
                })}
            </div>
        </motion.div>
    );
}
