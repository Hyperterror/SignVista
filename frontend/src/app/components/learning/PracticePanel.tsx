"use client";

import { motion } from "framer-motion";
import { Sparkles, Activity } from "lucide-react";

const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];

export function PracticePanel() {
    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-5xl flex flex-col gap-8">

                {/* Word of the Day Card */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2, ease: AG_EASE }}
                    className="w-full bg-white dark:bg-gray-800 rounded-[24px] border border-gray-100 dark:border-gray-700 p-8 shadow-xl flex flex-col md:flex-row items-center gap-8 relative overflow-hidden"
                >
                    {/* Background Glow */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#63C1BB]/5 dark:bg-[#63C1BB]/10 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2" />

                    <div className="w-32 h-32 rounded-2xl bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center shrink-0 border border-gray-100 dark:border-gray-700">
                        <span className="text-5xl">🌞</span>
                    </div>

                    <div className="flex-1 text-center md:text-left z-10">
                        <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                            <Sparkles className="w-5 h-5 text-[#105F68] dark:text-[#9ED5D1]" />
                            <span className="text-sm font-bold text-[#105F68] dark:text-[#63C1BB] uppercase tracking-wider">Word of the Day</span>
                        </div>
                        <h2 className="text-4xl md:text-5xl font-black text-gray-900 dark:text-gray-100 mb-3">Morning</h2>
                        <p className="text-gray-600 dark:text-gray-400 text-lg max-w-xl font-medium">
                            Start your day by practicing this essential daily greeting. Focus on smooth, continuous hand motion.
                        </p>
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="px-8 py-4 bg-[#105F68] text-white dark:bg-[#63C1BB] dark:text-[#105F68] rounded-xl font-bold shadow-lg hover:shadow-xl transition-all shrink-0 z-10"
                    >
                        Practice Now
                    </motion.button>
                </motion.div>

                {/* Practice Exercises Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {[
                        { word: "Family", accuracy: 85, icon: "👨‍👩‍👧‍👦" },
                        { word: "Help", accuracy: 42, icon: "🆘" },
                    ].map((exercise, idx) => (
                        <motion.div
                            key={exercise.word}
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.4 + idx * 0.1, ease: AG_EASE }}
                            whileHover={{ y: -6, boxShadow: "0 12px 30px rgba(0,0,0,0.05)" }}
                            className="bg-white dark:bg-gray-800/80 backdrop-blur-md rounded-2xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col"
                        >
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-16 h-16 rounded-xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center text-3xl shrink-0">
                                    {exercise.icon}
                                </div>
                                <div className="flex-1">
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">{exercise.word}</h3>
                                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                        <Activity className="w-4 h-4" />
                                        <span>Last accuracy: {exercise.accuracy}%</span>
                                    </div>
                                </div>
                            </div>

                            {/* Accuracy Meter */}
                            <div className="w-full bg-gray-100 dark:bg-gray-900 h-3 rounded-full overflow-hidden mb-6 relative">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${exercise.accuracy}%` }}
                                    transition={{ duration: 1.5, delay: 0.6 + idx * 0.1, ease: AG_EASE }}
                                    className="h-full bg-gradient-to-r from-[#105F68] to-[#3A9295] dark:from-[#63C1BB] dark:to-[#9ED5D1] rounded-full"
                                />
                            </div>

                            <div className="mt-auto pt-4 border-t border-gray-50 dark:border-gray-700 flex justify-between items-center">
                                <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">Needs improvement</span>
                                <button className="text-sm font-bold text-[#105F68] dark:text-[#9ED5D1] hover:underline transition-all">Review Sign →</button>
                            </div>
                        </motion.div>
                    ))}
                </div>

            </div>
        </div>
    );
}
