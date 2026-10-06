"use client";

import { motion, AnimatePresence } from "framer-motion";
import { DictionaryPanel } from "./DictionaryPanel";
import { PracticePanel } from "./PracticePanel";
import { ProficiencyMatrixPanel } from "./ProficiencyMatrixPanel";
import { QuizGamePanel } from "./QuizGamePanel";
import { AG_EASE, DictionaryWord, ProgressWord, VocabularyWord } from "../../learning/types";

export type LearningTab = "dictionary" | "practice" | "matrix" | "quiz";

const TABS: { id: LearningTab; label: string }[] = [
    { id: "dictionary", label: "ISL Dictionary" },
    { id: "practice", label: "Practice" },
    { id: "matrix", label: "Proficiency Matrix" },
    { id: "quiz", label: "Quiz Game" },
];

interface Props {
    activeTab: LearningTab;
    onTabChange: (tab: LearningTab) => void;
    dictionary: DictionaryWord[];
    progress: ProgressWord[];
    vocabulary: VocabularyWord[];
    practiceWord: string | null;
    onPractice: (word: string) => void;
    onAttempt: () => void;
}

export function TabbedLearningPanel({ activeTab, onTabChange, dictionary, progress, vocabulary, practiceWord, onPractice, onAttempt }: Props) {
    return (
        <div className="w-full flex flex-col items-center">
            <motion.div
                initial={{ y: 80, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, ease: AG_EASE }}
                className="relative w-full md:w-3/4 max-w-4xl bg-[#63C1BB] rounded-full p-1.5 flex shadow-[0_12px_40px_rgba(99,193,187,0.3)] z-20 mb-8"
                role="tablist"
            >
                {TABS.map((tab, idx) => {
                    const isActive = activeTab === tab.id;
                    return (
                        <div key={tab.id} className="relative flex-1 flex items-center">
                            {idx > 0 && <div className="absolute left-0 h-1/2 w-[1px] bg-[#105F68]/30 -translate-x-1/2" />}
                            <motion.button
                                role="tab"
                                aria-selected={isActive}
                                whileHover={{ y: isActive ? 0 : -3 }}
                                onClick={() => onTabChange(tab.id)}
                                className={`w-full py-3.5 px-4 rounded-full text-sm sm:text-base font-bold transition-colors duration-300 relative z-10 ${isActive ? "text-white" : "text-[#344C3D] hover:text-[#105F68]"}`}
                            >
                                <span className="relative z-10">{tab.label}</span>
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTabUnderline"
                                        className="absolute bottom-2 left-1/2 -translate-x-1/2 w-8 h-[3px] bg-[#9ED5D1] rounded-full shadow-[0_0_8px_rgba(158,213,209,0.8)]"
                                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                                    />
                                )}
                            </motion.button>
                        </div>
                    );
                })}
            </motion.div>

            <div className="w-full max-w-7xl px-4 relative min-h-[600px] overflow-hidden">
                <AnimatePresence mode="popLayout" initial={false}>
                    <motion.div
                        key={activeTab}
                        initial={{ x: "100%", opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: "-100%", opacity: 0 }}
                        transition={{ duration: 0.6, ease: AG_EASE }}
                        className="w-full h-full"
                    >
                        {activeTab === "dictionary" && <DictionaryPanel words={dictionary} onPractice={onPractice} />}
                        {activeTab === "practice" && (
                            <PracticePanel
                                key={practiceWord ?? ''}
                                vocabulary={vocabulary}
                                progress={progress}
                                dictionary={dictionary}
                                initialWord={practiceWord}
                                onAttempt={onAttempt}
                            />
                        )}
                        {activeTab === "matrix" && <ProficiencyMatrixPanel progress={progress} dictionary={dictionary} onPractice={onPractice} />}
                        {activeTab === "quiz" && <QuizGamePanel dictionary={dictionary} />}
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
}
