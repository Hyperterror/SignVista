"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import { Clock, CheckCircle2, XCircle, Flame } from "lucide-react";

const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];

const OPTIONS = [
    { id: 1, text: "Happy" },
    { id: 2, text: "Sad" },
    { id: 3, text: "Angry", isCorrect: true },
    { id: 4, text: "Surprised" },
];

export function QuizGamePanel() {
    const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);

    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-4xl flex flex-col md:flex-row items-center gap-12 bg-white dark:bg-gray-800 rounded-[32px] border border-gray-100 dark:border-gray-700 p-8 shadow-2xl relative">

                {/* Streak Counter (Top Right) */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.6, type: "spring" }}
                    className="absolute top-6 right-8 flex items-center gap-2 bg-[#105F68] dark:bg-gray-900/80 py-2 px-4 rounded-full border border-[#63C1BB]/50 shadow-lg"
                >
                    <Flame className="w-5 h-5 text-[#9ED5D1] fill-current" />
                    <span className="font-black text-white dark:text-[#C8E6E2]">13 Streak</span>
                </motion.div>

                {/* Hero Area / GIF Container */}
                <div className="w-full md:w-1/2 flex flex-col items-center">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: AG_EASE }}
                        className="flex items-center gap-3 mb-8"
                    >
                        <Clock className="w-6 h-6 text-[#105F68] dark:text-[#9ED5D1]" />
                        <h2 className="text-3xl font-black text-gray-900 dark:text-gray-100 tracking-tight">Speed Challenge</h2>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2, ease: AG_EASE }}
                        className="w-full aspect-square max-w-[300px] bg-gray-50 dark:bg-gray-900 rounded-[32px] border-2 border-gray-100 dark:border-gray-700 shadow-inner flex items-center justify-center relative overflow-hidden"
                    >
                        {/* Timer visual ring */}
                        <svg className="absolute inset-0 w-full h-full -rotate-90 opacity-10">
                            <circle cx="50%" cy="50%" r="48%" stroke="#105F68" strokeWidth="8" fill="none" strokeDasharray="1000" />
                        </svg>
                        <span className="text-8xl">
                            😠
                        </span>
                    </motion.div>
                </div>

                {/* Answer Options */}
                <div className="w-full md:w-1/2 flex flex-col gap-4">
                    <p className="text-gray-500 dark:text-gray-400 font-black text-center md:text-left mb-2 uppercase tracking-widest text-xs">
                        What sign is this?
                    </p>
                    {OPTIONS.map((opt, idx) => {
                        const isSelected = selectedAnswer === opt.id;
                        const isAnswered = selectedAnswer !== null;
                        const isCorrectSel = isSelected && opt.isCorrect;
                        const isWrongSel = isSelected && !opt.isCorrect;
                        const showCorrect = isAnswered && opt.isCorrect;

                        return (
                            <motion.button
                                key={opt.id}
                                initial={{ opacity: 0, x: 40 }}
                                animate={{
                                    opacity: 1, x: 0,
                                    ...(isWrongSel && { x: [-10, 10, -10, 10, 0] })
                                }}
                                transition={{
                                    duration: isWrongSel ? 0.4 : 0.6,
                                    delay: isWrongSel ? 0 : 0.3 + idx * 0.1,
                                    ease: AG_EASE
                                }}
                                whileHover={!isAnswered ? { y: -4, scale: 1.02 } : {}}
                                whileTap={!isAnswered ? { scale: 0.98 } : {}}
                                onClick={() => !isAnswered && setSelectedAnswer(opt.id)}
                                disabled={isAnswered}
                                className={`
                  relative w-full py-5 px-6 rounded-2xl border-2 text-lg font-black flex justify-between items-center transition-all duration-300
                  ${!isAnswered ? 'bg-white dark:bg-gray-800/40 border-gray-100 dark:border-gray-700 text-gray-900 dark:text-gray-100 hover:border-[#63C1BB] hover:shadow-xl' : ''}
                  ${isCorrectSel || showCorrect ? 'bg-[#105F68] border-[#105F68] text-white shadow-lg' : ''}
                  ${isWrongSel ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 opacity-90' : ''}
                  ${isAnswered && !isSelected && !opt.isCorrect ? 'bg-gray-100 dark:bg-gray-900/40 border-transparent text-gray-400 dark:text-gray-600 opacity-40 grayscale' : ''}
                `}
                            >
                                <span>{opt.text}</span>

                                {isCorrectSel || showCorrect ? (
                                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                                        <CheckCircle2 className="w-6 h-6 text-white dark:text-[#9ED5D1]" />
                                    </motion.div>
                                ) : null}

                                {isWrongSel ? (
                                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                                        <XCircle className="w-6 h-6 text-red-500" />
                                    </motion.div>
                                ) : null}
                            </motion.button>
                        );
                    })}
                </div>

            </div>
        </div>
    );
}
