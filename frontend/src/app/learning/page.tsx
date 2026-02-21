"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { StatsDashboard } from '../components/learning/StatsDashboard';
import { TabbedLearningPanel } from '../components/learning/TabbedLearningPanel';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface Lesson {
    id: string;
    title: string;
    category: string;
    progress: number;
    totalSteps: number;
    completedSteps: number;
    locked: boolean;
    difficulty: string;
    icon: string;
}

interface Quiz {
    id: string;
    title: string;
    questions: number;
    score: number | null;
    difficulty: string;
}

export default function LearningPage() {
    const [lessons, setLessons] = useState<Lesson[]>([]);
    const [quizzes, setQuizzes] = useState<Quiz[]>([]);
    const [overallProgress, setOverallProgress] = useState(0);
    const [streak, setStreak] = useState(0);
    const [stats, setStats] = useState({ totalWords: 15, practicedWords: 0 });
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                const [progress, dashboard] = await Promise.all([
                    api.getProgress(),
                    api.getDashboard()
                ]);

                setOverallProgress(Math.round((progress?.overall_proficiency ?? 0) * 100));
                setStreak(dashboard?.current_streak ?? 0);
                setStats({
                    totalWords: dashboard?.total_achievements ?? 15, // Currently total available words
                    practicedWords: dashboard?.words_practiced ?? 0
                });

                const words = progress?.word_details || [];
                const categories = [...new Set(words.map((w: any) => w.category || 'Common'))];

                const mappedLessons: Lesson[] = categories.map((cat: any, idx) => {
                    const catWords = words.filter((w: any) => w.category === cat || (!w.category && cat === 'Common'));
                    const totalCatProficiency = catWords.reduce((acc: number, w: any) => acc + w.proficiency, 0);
                    const avgProficiency = catWords.length > 0 ? (totalCatProficiency / catWords.length) * 100 : 0;

                    return {
                        id: cat.toLowerCase(),
                        title: `${cat} Signs`,
                        category: cat as string,
                        progress: Math.round(avgProficiency),
                        totalSteps: catWords.length,
                        completedSteps: catWords.filter((w: any) => w.proficiency >= 0.8).length,
                        locked: idx > 0 && (progress?.overall_proficiency ?? 0) < 0.2, // Simple unlock logic
                        difficulty: idx === 0 ? 'Beginner' : idx === 1 ? 'Intermediate' : 'Advanced',
                        icon: cat === 'Greetings' ? '👋' : cat === 'Family' ? '👨‍👩‍👧‍👦' : '📚'
                    };
                });

                setLessons(mappedLessons);
                setQuizzes(categories.slice(0, 3).map((cat: any) => ({
                    id: `quiz-${cat}`,
                    title: `${cat} Mastery`,
                    questions: 10,
                    score: null,
                    difficulty: 'Medium'
                })));

            } catch (error) {
                console.error(error);
                toast.error('Failed to load learning data');
            } finally {
                setIsLoading(false);
            }
        };

        const animateIn = () => {
            if (document.querySelector('.stats-card')) {
                gsap.fromTo(
                    '.stats-card',
                    { y: 50, opacity: 0 },
                    { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'back.out(1.7)' }
                );
            }

            if (document.querySelector('.lesson-card')) {
                gsap.fromTo(
                    '.lesson-card',
                    { x: -50, opacity: 0 },
                    { x: 0, opacity: 1, duration: 0.6, stagger: 0.1, delay: 0.3, ease: 'power3.out' }
                );
            }
        };

        fetchData().then(() => {
            requestAnimationFrame(animateIn);
        });
    }, []);

    const startLesson = (lesson: Lesson) => {
        if (!lesson.locked) {
            gsap.to(`.lesson-${lesson.id}`, {
                scale: 0.95,
                duration: 0.1,
                yoyo: true,
                repeat: 1,
            });
            toast.info(`Starting ${lesson.title}...`);
        } else {
            toast.error('Complete previous lessons to unlock!');
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6">
                <div className="w-16 h-16 border-4 border-violet-600 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-gray-600 dark:text-gray-400 font-medium">Crunching your progress...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-6 md:p-12 relative overflow-hidden bg-[#F8FAFA] dark:bg-[#0a0a0a] transition-colors duration-500 font-sans selection:bg-[#9ED5D1] selection:text-[#105F68]">
            {/* Ambient Background Glows */}
            <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-[#63C1BB]/5 dark:bg-[#63C1BB]/10 rounded-full blur-[120px] -translate-y-1/2 -translate-x-1/2 pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-[#9ED5D1]/5 rounded-full blur-[150px] translate-y-1/4 translate-x-1/4 pointer-events-none" />

            <div className="max-w-7xl mx-auto relative z-10 flex flex-col items-center">
                {/* Header Phase */}
                <div className="mb-12 w-full text-center md:text-left space-y-2">
                    <h1 className="text-5xl md:text-6xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
                        Learning Hub
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400 font-medium max-w-2xl">
                        Track your progress and master Indian Sign Language in an immersive environment.
                    </p>
                </div>

                {/* Main Dashboard Cards */}
                <StatsDashboard
                    totalWords={stats.totalWords}
                    practiced={stats.practicedWords}
                    proficiency={overallProgress}
                    streak={streak}
                />

                {/* Tabbed Interactive Area */}
                <TabbedLearningPanel />
            </div>
        </div>
    );
}
