"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import gsap from 'gsap';
import { toast } from 'sonner';
import { StatsDashboard } from '../components/learning/StatsDashboard';
import { LearningTab, TabbedLearningPanel } from '../components/learning/TabbedLearningPanel';
import { api } from '../utils/api';
import { DictionaryWord, ProgressWord, VocabularyWord } from './types';

function LearningHub() {
    // Deep link from the dashboard/dictionary: /learning?practice=<word>
    const initialPractice = useSearchParams().get('practice');
    const [dictionary, setDictionary] = useState<DictionaryWord[]>([]);
    const [progress, setProgress] = useState<ProgressWord[]>([]);
    const [vocabulary, setVocabulary] = useState<VocabularyWord[]>([]);
    const [stats, setStats] = useState({ totalWords: 0, practiced: 0, proficiency: 0, streak: 0 });
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<LearningTab>(initialPractice ? 'practice' : 'dictionary');
    const [practiceWord, setPracticeWord] = useState<string | null>(initialPractice);
    const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const loadProgress = useCallback(async () => {
        const [prog, dash] = await Promise.all([api.getProgress(), api.getDashboard()]);
        setProgress(prog.word_details || []);
        setStats((s) => ({
            ...s,
            practiced: prog.words_practiced ?? 0,
            proficiency: Math.round(prog.overall_proficiency ?? 0),
            streak: dash.current_streak ?? 0,
        }));
    }, []);

    useEffect(() => {
        (async () => {
            try {
                const [dict, vocab] = await Promise.all([api.getDictionary(), api.getVocabulary()]);
                setDictionary(dict.words || []);
                setVocabulary(vocab.words || []);
                setStats((s) => ({
                    ...s,
                    totalWords: (dict.words || []).filter((w: DictionaryWord) => w.category !== 'alphabet').length,
                }));
                await loadProgress();
            } catch (error: any) {
                toast.error(error.message || 'Failed to load learning data');
            } finally {
                setIsLoading(false);
            }
        })();
    }, [loadProgress]);

    useEffect(() => {
        if (!isLoading && document.querySelector('.stats-card')) {
            gsap.fromTo('.stats-card', { y: 50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'back.out(1.7)' });
        }
    }, [isLoading]);

    useEffect(() => () => { if (refreshTimer.current) clearTimeout(refreshTimer.current); }, []);

    const handlePractice = (word: string) => {
        setPracticeWord(word);
        setActiveTab('practice');
    };

    // Refresh stats shortly after a recorded attempt (debounced)
    const handleAttempt = () => {
        if (refreshTimer.current) clearTimeout(refreshTimer.current);
        refreshTimer.current = setTimeout(() => { loadProgress().catch(() => { }); }, 800);
    };

    if (isLoading) return <LoadingState />;

    return (
        <div className="min-h-screen p-6 md:p-12 relative overflow-hidden bg-[#F8FAFA] dark:bg-[#0a0a0a] transition-colors duration-500 font-sans selection:bg-[#9ED5D1] selection:text-[#105F68]">
            <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#63C1BB]/5 dark:bg-[#63C1BB]/10 rounded-full blur-[120px] -translate-y-1/2 -translate-x-1/2 pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-[#9ED5D1]/5 rounded-full blur-[150px] translate-y-1/4 translate-x-1/4 pointer-events-none" />

            <div className="max-w-7xl mx-auto relative z-10 flex flex-col items-center">
                <div className="mb-12 w-full text-center md:text-left space-y-2">
                    <h1 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-gray-100 tracking-tight">Learning Hub</h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400 font-medium max-w-2xl">
                        Track your progress and master Indian Sign Language in an immersive environment.
                    </p>
                </div>

                <StatsDashboard
                    totalWords={stats.totalWords}
                    practiced={stats.practiced}
                    proficiency={stats.proficiency}
                    streak={stats.streak}
                />

                <TabbedLearningPanel
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    dictionary={dictionary}
                    progress={progress}
                    vocabulary={vocabulary}
                    practiceWord={practiceWord}
                    onPractice={handlePractice}
                    onAttempt={handleAttempt}
                />
            </div>
        </div>
    );
}

function LoadingState() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6">
            <div className="w-16 h-16 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-gray-600 dark:text-gray-400 font-medium">Crunching your progress...</p>
        </div>
    );
}

export default function LearningPage() {
    return (
        <Suspense fallback={<LoadingState />}>
            <LearningHub />
        </Suspense>
    );
}
