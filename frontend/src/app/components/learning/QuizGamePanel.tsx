"use client";

import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, XCircle, Flame, RefreshCw } from "lucide-react";
import { SignMedia } from "../SignMedia";
import { AG_EASE, DictionaryWord } from "../../learning/types";

const ROUNDS = 10;

interface Question {
    answer: DictionaryWord;
    options: DictionaryWord[];
}

function shuffle<T>(items: T[]): T[] {
    const a = [...items];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

/** "Which sign is this?" — built from the real ISL dictionary. */
export function QuizGamePanel({ dictionary }: { dictionary: DictionaryWord[] }) {
    const pool = useMemo(() => dictionary.filter((w) => w.category !== "alphabet"), [dictionary]);
    const [question, setQuestion] = useState<Question | null>(null);
    const [selected, setSelected] = useState<string | null>(null);
    const [round, setRound] = useState(1);
    const [score, setScore] = useState(0);
    const [streak, setStreak] = useState(0);
    const [bestStreak, setBestStreak] = useState(0);
    const [finished, setFinished] = useState(false);

    const nextQuestion = useCallback(() => {
        if (pool.length < 4) return;
        const answer = pool[Math.floor(Math.random() * pool.length)];
        const distractors = shuffle(pool.filter((w) => w.word !== answer.word)).slice(0, 3);
        setQuestion({ answer, options: shuffle([answer, ...distractors]) });
        setSelected(null);
    }, [pool]);

    useEffect(() => { nextQuestion(); }, [nextQuestion]);

    const choose = (word: string) => {
        if (selected || !question) return;
        setSelected(word);
        if (word === question.answer.word) {
            setScore((s) => s + 1);
            setStreak((s) => {
                const next = s + 1;
                setBestStreak((b) => Math.max(b, next));
                return next;
            });
        } else {
            setStreak(0);
        }
    };

    const advance = () => {
        if (round >= ROUNDS) {
            setFinished(true);
            return;
        }
        setRound((r) => r + 1);
        nextQuestion();
    };

    const restart = () => {
        setRound(1);
        setScore(0);
        setStreak(0);
        setFinished(false);
        nextQuestion();
    };

    if (pool.length < 4) {
        return <p className="text-center text-gray-500 py-12">Not enough signs in the dictionary for a quiz yet.</p>;
    }

    if (finished) {
        return (
            <div className="w-full flex justify-center py-4">
                <div className="w-full max-w-xl bg-white dark:bg-gray-800 rounded-[32px] p-10 text-center shadow-2xl border border-gray-100 dark:border-gray-700">
                    <h2 className="text-4xl font-black text-gray-900 dark:text-gray-100">{score} / {ROUNDS}</h2>
                    <p className="text-gray-500 mt-2">Best streak: {bestStreak}</p>
                    <button onClick={restart} className="mt-8 px-8 py-4 rounded-2xl bg-[#105F68] text-white font-bold inline-flex items-center gap-2">
                        <RefreshCw className="w-5 h-5" /> Play again
                    </button>
                </div>
            </div>
        );
    }

    if (!question) return null;

    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-4xl flex flex-col md:flex-row items-center gap-12 bg-white dark:bg-gray-800 rounded-[32px] border border-gray-100 dark:border-gray-700 p-8 shadow-2xl relative">
                <div className="absolute top-6 right-8 flex items-center gap-2 bg-[#105F68] dark:bg-gray-900/80 py-2 px-4 rounded-full border border-[#63C1BB]/50 shadow-lg">
                    <Flame className="w-5 h-5 text-[#9ED5D1] fill-current" />
                    <span className="font-black text-white dark:text-[#C8E6E2]">{streak} Streak</span>
                </div>

                <div className="w-full md:w-1/2 flex flex-col items-center pt-10 md:pt-0">
                    <p className="text-sm font-bold text-gray-400 mb-4">Question {round} of {ROUNDS} · Score {score}</p>
                    <SignMedia
                        gifUrl={question.answer.gif_url}
                        label="?"
                        className="w-full aspect-square max-w-[300px] rounded-[32px] border-2 border-gray-100 dark:border-gray-700"
                    />
                    <p className="mt-6 text-gray-600 dark:text-gray-300 text-center font-medium">
                        {question.answer.description}
                    </p>
                </div>

                <div className="w-full md:w-1/2 flex flex-col gap-4">
                    <p className="text-gray-500 dark:text-gray-400 font-black text-center md:text-left mb-2 uppercase tracking-widest text-xs">
                        Which sign is this?
                    </p>
                    {question.options.map((opt, idx) => {
                        const isAnswered = selected !== null;
                        const isSelected = selected === opt.word;
                        const isCorrect = opt.word === question.answer.word;
                        return (
                            <motion.button
                                key={`${round}-${opt.word}`}
                                initial={{ opacity: 0, x: 40 }}
                                animate={{ opacity: 1, x: 0, ...(isSelected && !isCorrect && { x: [-10, 10, -10, 10, 0] }) }}
                                transition={{ duration: 0.5, delay: isAnswered ? 0 : 0.1 + idx * 0.08, ease: AG_EASE }}
                                onClick={() => choose(opt.word)}
                                disabled={isAnswered}
                                className={`w-full py-5 px-6 rounded-2xl border-2 text-lg font-black flex justify-between items-center transition-all duration-300
                                    ${!isAnswered ? 'bg-white dark:bg-gray-800/40 border-gray-100 dark:border-gray-700 text-gray-900 dark:text-gray-100 hover:border-[#63C1BB] hover:shadow-xl' : ''}
                                    ${isAnswered && isCorrect ? 'bg-[#105F68] border-[#105F68] text-white shadow-lg' : ''}
                                    ${isSelected && !isCorrect ? 'bg-red-50 dark:bg-red-900/20 border-red-200 text-red-600' : ''}
                                    ${isAnswered && !isSelected && !isCorrect ? 'opacity-40 border-transparent' : ''}`}
                            >
                                <span>{opt.display_name}</span>
                                {isAnswered && isCorrect && <CheckCircle2 className="w-6 h-6" />}
                                {isSelected && !isCorrect && <XCircle className="w-6 h-6 text-red-500" />}
                            </motion.button>
                        );
                    })}
                    {selected && (
                        <button onClick={advance} className="mt-2 py-4 rounded-2xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-bold">
                            {round >= ROUNDS ? 'See results' : 'Next question →'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
