"use client";

import { useState, useEffect } from 'react';
import gsap from 'gsap';
import { Trophy, Target, BookOpen, CheckCircle, Lock, Play, Star, TrendingUp } from 'lucide-react';
import { Progress } from '../components/ui/progress';
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
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                const [progress, dashboard] = await Promise.all([
                    api.getProgress(),
                    api.getDashboard()
                ]);

                setOverallProgress(Math.round(progress.overall_proficiency * 100));
                setStreak(dashboard.current_streak);

                const words = progress.word_details || [];
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
                        locked: idx > 0 && progress.overall_proficiency < 0.2, // Simple unlock logic
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

        fetchData();

        // Entrance animations
        gsap.fromTo(
            '.stats-card',
            { y: 50, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.6, stagger: 0.1, ease: 'back.out(1.7)' }
        );

        gsap.fromTo(
            '.lesson-card',
            { x: -50, opacity: 0 },
            { x: 0, opacity: 1, duration: 0.6, stagger: 0.1, delay: 0.3, ease: 'power3.out' }
        );
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
        <div className="min-h-screen p-6 md:p-12">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                        Learning Hub
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400">
                        Track your progress and master ISL step by step
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    <div className="stats-card bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl p-6 text-white shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <Trophy className="w-8 h-8" />
                            <div className="text-3xl font-bold">{overallProgress}%</div>
                        </div>
                        <div className="text-sm opacity-90">Overall Progress</div>
                    </div>

                    <div className="stats-card bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl p-6 text-white shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <Target className="w-8 h-8" />
                            <div className="text-3xl font-bold">{streak}</div>
                        </div>
                        <div className="text-sm opacity-90">Day Streak 🔥</div>
                    </div>

                    <div className="stats-card bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <BookOpen className="w-8 h-8" />
                            <div className="text-3xl font-bold">{lessons.filter(l => l.progress === 100).length}</div>
                        </div>
                        <div className="text-sm opacity-90">Lessons Completed</div>
                    </div>

                    <div className="stats-card bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-xl">
                        <div className="flex items-center justify-between mb-3">
                            <Star className="w-8 h-8" />
                            <div className="text-3xl font-bold">{overallProgress * 10}</div>
                        </div>
                        <div className="text-sm opacity-90">Total XP</div>
                    </div>
                </div>

                {/* Main Content */}
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Lessons Section */}
                    <div className="lg:col-span-2">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                                Your Learning Path
                            </h2>
                        </div>

                        <div className="space-y-4">
                            {lessons.map((lesson) => (
                                <div
                                    key={lesson.id}
                                    className={`
                    lesson-card lesson-${lesson.id}
                    relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700
                    transition-all duration-300 cursor-pointer
                    ${lesson.locked ? 'opacity-60' : 'hover:shadow-2xl hover:-translate-y-1'}
                  `}
                                    onClick={() => startLesson(lesson)}
                                >
                                    {lesson.locked && (
                                        <div className="absolute top-4 right-4 p-2 bg-gray-200 dark:bg-gray-700 rounded-lg">
                                            <Lock className="w-5 h-5 text-gray-500" />
                                        </div>
                                    )}

                                    <div className="flex items-start gap-4">
                                        <div className="text-5xl">{lesson.icon}</div>
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                                                        {lesson.title}
                                                    </h3>
                                                    <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                                                        <span className="px-2 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full text-xs font-medium">
                                                            {lesson.category}
                                                        </span>
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700`}>
                                                            {lesson.difficulty}
                                                        </span>
                                                    </div>
                                                </div>
                                                {!lesson.locked && lesson.progress === 100 && (
                                                    <CheckCircle className="w-6 h-6 text-green-500" />
                                                )}
                                            </div>
                                            <div className="mt-4">
                                                <div className="flex items-center justify-between text-sm mb-2">
                                                    <span className="text-gray-600 dark:text-gray-400">
                                                        {lesson.completedSteps} / {lesson.totalSteps} steps
                                                    </span>
                                                    <span className="font-semibold text-violet-600 dark:text-violet-400">
                                                        {lesson.progress}%
                                                    </span>
                                                </div>
                                                <Progress value={lesson.progress} className="h-2" />
                                            </div>
                                            {!lesson.locked && (
                                                <button className="mt-4 px-6 py-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all duration-300 flex items-center gap-2">
                                                    <Play className="w-4 h-4" />
                                                    {lesson.progress === 0 ? 'Start Lesson' : lesson.progress === 100 ? 'Review' : 'Continue'}
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                                <Target className="w-6 h-6 text-violet-600" />
                                Practice Quizzes
                            </h3>
                            <div className="space-y-3">
                                {quizzes.map((quiz) => (
                                    <div key={quiz.id} className="p-4 bg-violet-50 dark:bg-gray-900 rounded-xl">
                                        <div className="flex items-center justify-between mb-2">
                                            <h4 className="font-semibold text-gray-900 dark:text-gray-100">{quiz.title}</h4>
                                        </div>
                                        <p className="text-xs text-gray-500 mb-3">{quiz.questions} questions</p>
                                        <button className="w-full px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium">Start</button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
