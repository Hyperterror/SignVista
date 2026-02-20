'use client';

import { motion } from 'framer-motion';
import { Edit2, ChevronLeft, ChevronRight, Mail } from 'lucide-react';

const easeBounce: [number, number, number, number] = [0.34, 1.56, 0.64, 1];

export function RightProfilePanel() {
    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: easeBounce }}
            className="w-[320px] shrink-0 h-full border-l border-[#63C1BB]/20 bg-white/10 dark:bg-[#0a0a0a]/20 backdrop-blur-2xl p-6 flex flex-col shadow-[-10px_0_30px_rgba(16,95,104,0.2)]"
        >
            {/* Top Banner: Profile Title + Edit Icon */}
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-[#9ED5D1] font-bold text-xl drop-shadow-md">Profile</h2>
                <motion.button
                    whileHover={{ translateY: -3, scale: 1.1 }}
                    transition={{ ease: easeBounce }}
                    className="text-[#63C1BB] hover:text-[#9ED5D1] transition-colors"
                >
                    <Edit2 size={18} />
                </motion.button>
            </div>

            {/* User Avatar & Info */}
            <div className="flex flex-col items-center mb-10">
                <motion.div
                    whileHover={{ translateY: -5, boxShadow: '0 10px 25px rgba(99,193,187,0.4)' }}
                    transition={{ ease: easeBounce }}
                    className="w-24 h-24 rounded-full bg-gradient-to-tr from-[#105F68] to-[#63C1BB] p-1 shadow-[0_5px_15px_rgba(16,95,104,0.3)] mb-4 cursor-pointer"
                >
                    <div className="w-full h-full rounded-full bg-[#3A9295] flex items-center justify-center text-3xl font-bold text-white shadow-inner">
                        P
                    </div>
                </motion.div>

                <h3 className="text-white font-bold text-lg tracking-wide drop-shadow-md">Purvi Jain</h3>
                <p className="text-[#BFCFBB] text-sm font-medium mt-1">purvi.j@signvista.com</p>
            </div>

            {/* Scrollable Metrics & Schedule Area */}
            <div className="flex-1 overflow-y-auto pr-2 scrollbar-hide space-y-8">

                {/* Mock Calendar Widget */}
                <motion.div
                    whileHover={{ translateY: -4 }}
                    transition={{ ease: easeBounce }}
                    className="bg-white/5 border border-[#63C1BB]/30 rounded-2xl p-4 shadow-[0_5px_20px_rgba(16,95,104,0.15)]"
                >
                    <div className="flex justify-between items-center text-[#9ED5D1] mb-4">
                        <ChevronLeft size={16} className="cursor-pointer hover:text-white" />
                        <span className="font-semibold text-sm">May 2026</span>
                        <ChevronRight size={16} className="cursor-pointer hover:text-white" />
                    </div>

                    <div className="grid grid-cols-7 gap-1 text-center text-xs mb-2 text-[#8EA58C]">
                        <div>S</div><div>M</div><div>T</div><div>W</div><div>T</div><div>F</div><div>S</div>
                    </div>

                    <div className="grid grid-cols-7 gap-1 text-center text-sm text-[#C8E6E2]">
                        <div className="py-1 opacity-50">26</div>
                        <div className="py-1 opacity-50">27</div>
                        <div className="py-1 opacity-50">28</div>
                        <div className="py-1 opacity-50">29</div>
                        <div className="py-1 opacity-50">30</div>
                        <div className="py-1">1</div>
                        <div className="py-1">2</div>

                        {/* Active streak day highlighted */}
                        <div className="py-1">3</div>
                        <div className="py-1 bg-gradient-to-b from-[#105F68] to-[#344C3D] rounded-full border border-[#63C1BB] shadow-[0_0_10px_#63C1BB] font-bold text-white relative">
                            4
                            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-[#9ED5D1] rounded-full"></div>
                        </div>
                        <div className="py-1">5</div>
                        <div className="py-1">6</div>
                        <div className="py-1">7</div>
                        <div className="py-1">8</div>
                        <div className="py-1">9</div>
                    </div>
                </motion.div>

                {/* Schedule */}
                <div>
                    <div className="flex justify-between items-end mb-4">
                        <h3 className="text-[#9ED5D1] font-semibold text-lg drop-shadow">Schedule</h3>
                        <span className="text-xs text-[#8EA58C] hover:text-white cursor-pointer transition-colors">See all</span>
                    </div>

                    <div className="space-y-3">
                        <motion.div
                            whileHover={{ translateY: -4, x: 2 }}
                            transition={{ ease: easeBounce }}
                            className="relative overflow-hidden bg-gradient-to-r from-white/10 to-transparent border border-white/5 rounded-xl p-4 pl-5 shadow-sm group cursor-pointer"
                        >
                            <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#63C1BB] group-hover:bg-[#9ED5D1] shadow-[0_0_8px_#63C1BB] transition-colors" />
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-[#9ED5D1] font-bold text-sm">12:00</span>
                                <span className="text-xs text-[#8EA58C] bg-[#105F68]/40 px-2 py-0.5 rounded-full">Live Session</span>
                            </div>
                            <p className="text-white font-medium text-sm">Intro to Finger Spelling</p>
                            <p className="text-xs text-[#BFCFBB] mt-1">Module 1 • Beginner</p>
                        </motion.div>

                        <motion.div
                            whileHover={{ translateY: -4, x: 2 }}
                            transition={{ ease: easeBounce }}
                            className="relative overflow-hidden bg-gradient-to-r from-white/10 to-transparent border border-white/5 rounded-xl p-4 pl-5 shadow-sm group cursor-pointer"
                        >
                            <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#3A9295] group-hover:bg-[#63C1BB] transition-colors" />
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-[#9ED5D1] font-bold text-sm">14:30</span>
                                <span className="text-xs text-[#8EA58C] bg-[#105F68]/40 px-2 py-0.5 rounded-full">Practice</span>
                            </div>
                            <p className="text-white font-medium text-sm">Everyday Greetings Review</p>
                            <p className="text-xs text-[#BFCFBB] mt-1">Module 2 • Review</p>
                        </motion.div>
                    </div>
                </div>

                {/* Reminders */}
                <div>
                    <h3 className="text-[#9ED5D1] font-semibold text-lg drop-shadow mb-4">Reminders</h3>
                    <motion.div
                        whileHover={{ translateY: -3 }}
                        transition={{ ease: easeBounce }}
                        className="flex items-center space-x-4 bg-white/5 border border-white/10 rounded-xl p-3 cursor-pointer hover:bg-white/10 transition-colors"
                    >
                        <div className="w-10 h-10 rounded-lg bg-[#105F68]/40 flex items-center justify-center text-[#63C1BB]">
                            <Mail size={18} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-white">Weekly Progress Report</p>
                            <p className="text-xs text-[#8EA58C]">Check your email inbox</p>
                        </div>
                    </motion.div>
                </div>

            </div>

            {/* Profile & Theme Floating Button (Bottom of panel to fit nicely, or customized top right fixed) */}
            <div className="mt-6 pt-4 border-t border-white/10 relative">
                <motion.button
                    whileHover={{ translateY: -5 }}
                    transition={{ ease: easeBounce }}
                    className="w-full relative group"
                >
                    {/* Pulsing ring behind */}
                    <div className="absolute inset-0 bg-[#9ED5D1] rounded-full animate-ping opacity-20 duration-1000"></div>

                    <div className="relative w-full py-3 rounded-full bg-[#63C1BB] text-[#344C3D] font-bold text-sm flex items-center justify-center shadow-[0_5px_15px_rgba(99,193,187,0.4)] group-hover:shadow-[0_8px_25px_rgba(158,213,209,0.7)] group-hover:bg-[#9ED5D1] transition-all">
                        Profile & Theme Settings
                    </div>
                </motion.button>
            </div>
        </motion.div>
    );
}
