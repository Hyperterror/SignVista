"use client";

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Search, Filter, Play, Star, BookmarkPlus, BookmarkCheck, Target, Camera, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface DictionaryWord {
    word: string;
    hindi_name: string;
    category: string;
    gesture: string;
    description: string;
    difficulty: string;
    tips: string[];
    gif_url?: string;
}

interface ProficiencyResult {
    score: number;
    level: string;
    feedback: string;
    accuracy: number;
    avgConfidence: number;
    attempts: Array<{
        predicted: string;
        confidence: number;
        correct: boolean;
    }>;
}

export default function DictionaryPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [words, setWords] = useState<DictionaryWord[]>([]);
    const [filteredWords, setFilteredWords] = useState<DictionaryWord[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [testingWord, setTestingWord] = useState<string | null>(null);
    const [testingProgress, setTestingProgress] = useState(0);
    const [proficiencyResult, setProficiencyResult] = useState<ProficiencyResult | null>(null);
    const searchRef = useRef<HTMLInputElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        const fetchWords = async () => {
            try {
                setIsLoading(true);
                const data = await api.getDictionary();
                setWords(data.words);
                setFilteredWords(data.words);
            } catch (error) {
                console.error(error);
                toast.error('Failed to load dictionary');
            } finally {
                setIsLoading(false);
            }
        };

        fetchWords();

        // Entrance animation
        gsap.fromTo(
            '.search-bar',
            { y: -50, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }
        );

        gsap.fromTo(
            '.category-filter',
            { y: -30, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.6, delay: 0.1, ease: 'power3.out' }
        );
    }, []);

    useEffect(() => {
        // Filter words
        let filtered = words;

        if (searchQuery) {
            filtered = filtered.filter(word =>
                word.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
                word.category.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        if (selectedCategory !== 'All') {
            filtered = filtered.filter(word => word.category === selectedCategory);
        }

        setFilteredWords(filtered);

        // Animate cards
        gsap.fromTo(
            '.word-card',
            { scale: 0.9, opacity: 0, y: 20 },
            {
                scale: 1,
                opacity: 1,
                y: 0,
                duration: 0.4,
                stagger: 0.05,
                ease: 'back.out(1.7)'
            }
        );
    }, [searchQuery, selectedCategory, words]);

    const playSign = (word: string) => {
        toast.success(`Playing sign for "${word}"`);
    };

    const startProficiencyTest = async (word: string) => {
        setTestingWord(word);
        setTestingProgress(0);
        setProficiencyResult(null);

        try {
            // Start camera
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }

            toast.info(`Get ready to perform the sign for "${word}" 5 times!`);
            
            // Wait 3 seconds before starting
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Capture 5 attempts
            const attempts = [];
            for (let i = 0; i < 5; i++) {
                setTestingProgress(i + 1);
                toast.info(`Attempt ${i + 1}/5 - Show the sign now!`);
                
                // Capture frame
                const frame = captureFrame();
                if (!frame) continue;

                // Get prediction
                const result = await api.recognizeFrame(frame);
                
                attempts.push({
                    predicted: result.word,
                    confidence: result.confidence,
                    correct: result.word?.toLowerCase() === word.toLowerCase()
                });

                // Wait 2 seconds between attempts
                if (i < 4) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            }

            // Calculate proficiency
            const correctAttempts = attempts.filter(a => a.correct);
            const accuracy = correctAttempts.length / attempts.length;
            const avgConfidence = correctAttempts.length > 0
                ? correctAttempts.reduce((sum, a) => sum + a.confidence, 0) / correctAttempts.length
                : 0;

            // Calculate proficiency score
            const baseScore = avgConfidence * 50;
            const accuracyScore = accuracy * 30;
            const consistencyScore = calculateConsistency(attempts) * 20;
            const totalScore = Math.min(100, baseScore + accuracyScore + consistencyScore);

            let level = 'Beginner';
            let feedback = 'Keep practicing!';
            
            if (totalScore >= 85) {
                level = 'Expert';
                feedback = 'Excellent sign clarity and consistency!';
            } else if (totalScore >= 70) {
                level = 'Advanced';
                feedback = 'Great job! Keep practicing for perfection.';
            } else if (totalScore >= 50) {
                level = 'Intermediate';
                feedback = 'Good progress! Focus on clarity and consistency.';
            }

            setProficiencyResult({
                score: Math.round(totalScore),
                level,
                feedback,
                accuracy,
                avgConfidence,
                attempts
            });

            toast.success(`Test complete! Your proficiency: ${level}`);

        } catch (error) {
            console.error('Proficiency test error:', error);
            toast.error('Failed to complete proficiency test');
        } finally {
            // Stop camera
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                setStream(null);
            }
        }
    };

    const captureFrame = (): string | null => {
        if (!videoRef.current) return null;

        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;

        ctx.drawImage(videoRef.current, 0, 0, 640, 480);
        return canvas.toDataURL('image/jpeg', 0.6);
    };

    const calculateConsistency = (attempts: Array<{ confidence: number }>): number => {
        if (attempts.length < 2) return 0;
        
        const confidences = attempts.map(a => a.confidence);
        const mean = confidences.reduce((sum, c) => sum + c, 0) / confidences.length;
        const variance = confidences.reduce((sum, c) => sum + Math.pow(c - mean, 2), 0) / confidences.length;
        
        // Lower variance = higher consistency (invert and normalize)
        return Math.max(0, 1 - variance);
    };

    const closeProficiencyTest = () => {
        setTestingWord(null);
        setTestingProgress(0);
        setProficiencyResult(null);
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    const categories = ['All', ...new Set(words.map(w => w.category))];

    return (
        <div className="min-h-screen p-6 md:p-12">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                        SignVista Dictionary
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400">
                        Explore {words.length} Indian Sign Language words with video demonstrations
                    </p>
                </div>

                {/* Search Bar */}
                <div className="search-bar mb-8">
                    <div className="relative">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-400" />
                        <input
                            ref={searchRef}
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search for signs, words, or categories..."
                            className="w-full pl-16 pr-6 py-5 rounded-2xl bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 focus:border-violet-500 dark:focus:border-violet-500 outline-none text-lg shadow-lg transition-all duration-300"
                        />
                    </div>
                </div>

                {/* Category Filter */}
                <div className="category-filter mb-12">
                    <div className="flex items-center gap-3 mb-4">
                        <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        <span className="font-semibold text-gray-900 dark:text-gray-100">Categories</span>
                    </div>
                    <div className="flex flex-wrap gap-3">
                        {categories.map((category) => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`
                  px-6 py-3 rounded-xl font-medium transition-all duration-300
                  ${selectedCategory === category
                                        ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg scale-105'
                                        : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
                                    }
                `}
                            >
                                {category}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Results Count */}
                {!isLoading && (
                    <div className="mb-6 text-gray-600 dark:text-gray-400">
                        Showing {filteredWords.length} {filteredWords.length === 1 ? 'sign' : 'signs'}
                    </div>
                )}

                {/* Dictionary Grid */}
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="w-16 h-16 border-4 border-[#344C3D] border-t-transparent rounded-full animate-spin mb-4" />
                        <p className="text-gray-600 dark:text-gray-400 font-medium">Loading signs...</p>
                    </div>
                ) : (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {filteredWords.map((word) => (
                            <div
                                key={word.word}
                                className="word-card group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300 cursor-pointer overflow-hidden"
                            >
                                <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                <div className="relative z-10">
                                    <div className="flex items-center justify-between mb-4">
                                        <span className="text-xs px-3 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full font-medium">
                                            {word.category}
                                        </span>
                                    </div>
                                    <div className="text-7xl text-center mb-2 group-hover:scale-110 transition-transform duration-300">
                                        {word.gesture}
                                    </div>
                                    <div className="text-center mb-4">
                                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{word.word}</h3>
                                        <p className="text-sm text-[#105F68] dark:text-[#63C1BB] font-medium">{word.hindi_name}</p>
                                    </div>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 text-center line-clamp-2">{word.description}</p>
                                    <div className="flex items-center justify-center gap-2 mb-4">
                                        <span className={`
                      text-xs px-3 py-1 rounded-full font-medium
                      ${word.difficulty === 'easy' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : ''}
                      ${word.difficulty === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' : ''}
                      ${word.difficulty === 'hard' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : ''}
                    `}>
                                            {word.difficulty}
                                        </span>
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); startProficiencyTest(word.word); }}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-105"
                                    >
                                        <Target className="w-4 h-4" /> Test Proficiency
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {!isLoading && filteredWords.length === 0 && (
                    <div className="text-center py-20">
                        <div className="text-6xl mb-4">🔍</div>
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">No signs found</h3>
                        <p className="text-gray-600 dark:text-gray-400">Try adjusting your search or filter criteria</p>
                    </div>
                )}
            </div>

            {/* Proficiency Test Modal */}
            {testingWord && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
                    <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-4xl w-full p-8 shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                                Proficiency Test: {testingWord}
                            </h2>
                            <button
                                onClick={closeProficiencyTest}
                                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl"
                            >
                                ×
                            </button>
                        </div>

                        {!proficiencyResult ? (
                            <div className="space-y-6">
                                {/* Camera Feed */}
                                <div className="relative aspect-video bg-black rounded-2xl overflow-hidden">
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        playsInline
                                        muted
                                        className="w-full h-full object-cover scale-x-[-1]"
                                    />
                                    <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-4 py-2 rounded-full text-white font-semibold">
                                        <Camera className="w-4 h-4 inline mr-2" />
                                        Attempt {testingProgress}/5
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                                        <span>Progress</span>
                                        <span>{testingProgress}/5 attempts</span>
                                    </div>
                                    <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-violet-600 to-purple-600 transition-all duration-500"
                                            style={{ width: `${(testingProgress / 5) * 100}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="text-center text-gray-600 dark:text-gray-400">
                                    <p className="text-lg">Perform the sign clearly 5 times</p>
                                    <p className="text-sm mt-2">Make sure your hands are visible and well-lit</p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* Proficiency Score */}
                                <div className="text-center py-8">
                                    <div className="inline-block relative">
                                        <svg className="w-48 h-48 transform -rotate-90">
                                            <circle
                                                cx="96"
                                                cy="96"
                                                r="88"
                                                stroke="currentColor"
                                                strokeWidth="12"
                                                fill="none"
                                                className="text-gray-200 dark:text-gray-700"
                                            />
                                            <circle
                                                cx="96"
                                                cy="96"
                                                r="88"
                                                stroke="currentColor"
                                                strokeWidth="12"
                                                fill="none"
                                                strokeDasharray={`${2 * Math.PI * 88}`}
                                                strokeDashoffset={`${2 * Math.PI * 88 * (1 - proficiencyResult.score / 100)}`}
                                                className="text-violet-600 transition-all duration-1000"
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <div className="text-5xl font-black text-gray-900 dark:text-gray-100">
                                                {proficiencyResult.score}
                                            </div>
                                            <div className="text-sm text-gray-600 dark:text-gray-400">out of 100</div>
                                        </div>
                                    </div>
                                    <h3 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-4">
                                        {proficiencyResult.level}
                                    </h3>
                                    <p className="text-lg text-gray-600 dark:text-gray-400 mt-2">
                                        {proficiencyResult.feedback}
                                    </p>
                                </div>

                                {/* Stats */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="bg-violet-50 dark:bg-violet-900/20 rounded-xl p-4 text-center">
                                        <div className="text-3xl font-bold text-violet-600 dark:text-violet-400">
                                            {Math.round(proficiencyResult.accuracy * 100)}%
                                        </div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Accuracy</div>
                                    </div>
                                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 text-center">
                                        <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                                            {Math.round(proficiencyResult.avgConfidence * 100)}%
                                        </div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Avg Confidence</div>
                                    </div>
                                </div>

                                {/* Attempts Breakdown */}
                                <div className="space-y-2">
                                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">Attempt Details</h4>
                                    {proficiencyResult.attempts.map((attempt, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                                        >
                                            <div className="flex items-center gap-3">
                                                {attempt.correct ? (
                                                    <CheckCircle className="w-5 h-5 text-green-500" />
                                                ) : (
                                                    <XCircle className="w-5 h-5 text-red-500" />
                                                )}
                                                <span className="text-sm text-gray-700 dark:text-gray-300">
                                                    Attempt {idx + 1}: {attempt.predicted || 'No detection'}
                                                </span>
                                            </div>
                                            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                                                {Math.round(attempt.confidence * 100)}%
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Actions */}
                                <div className="flex gap-4">
                                    <button
                                        onClick={() => startProficiencyTest(testingWord)}
                                        className="flex-1 px-6 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold hover:scale-105 transition-transform"
                                    >
                                        Test Again
                                    </button>
                                    <button
                                        onClick={closeProficiencyTest}
                                        className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-xl font-semibold hover:scale-105 transition-transform"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
