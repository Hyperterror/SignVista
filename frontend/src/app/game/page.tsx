"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { Trophy, Timer, Zap, Target, RefreshCw, Play, Home } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface GameState {
    isActive: boolean;
    gameId: string | null;
    currentChallenge: string;
    score: number;
    streak: number;
    bestStreak: number;
    multiplier: number;
    timeLeft: number;
    wordsCompleted: number;
    isGameOver: boolean;
}

interface GameResult {
    score: number;
    wordsCompleted: number;
    totalChallenges: number;
    streak_best: number;
    accuracy: number;
    badges: string[];
}

const INITIAL_STATE: GameState = {
    isActive: false,
    gameId: null,
    currentChallenge: '',
    score: 0,
    streak: 0,
    bestStreak: 0,
    multiplier: 1,
    timeLeft: 30,
    wordsCompleted: 0,
    isGameOver: false,
};

const FRAME_INTERVAL_MS = 150;

const statusHint = (status: string): string => {
    if (status.startsWith('collecting')) return `Keep signing... ${status.split('_').pop()}`;
    if (status === 'no_hands') return 'Raise your hands into the frame';
    if (status === 'no_face') return 'Make sure your face is visible';
    return '';
};

export default function GamePage() {
    const router = useRouter();
    const [gameState, setGameState] = useState<GameState>(INITIAL_STATE);
    const [result, setResult] = useState<GameResult | null>(null);
    const [hint, setHint] = useState('');
    const [isStarting, setIsStarting] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const loopRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const gameStateRef = useRef(gameState);
    const endingRef = useRef(false);

    useEffect(() => {
        gameStateRef.current = gameState;
    }, [gameState]);

    useEffect(() => {
        gsap.fromTo('.game-header', { y: -20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8 });
        return () => {
            if (loopRef.current) clearTimeout(loopRef.current);
            streamRef.current?.getTracks().forEach((t) => t.stop());
        };
    }, []);

    const stopCamera = () => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
    };

    const startGame = async () => {
        if (isStarting) return;
        setIsStarting(true);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } });
            streamRef.current = stream;
        } catch {
            toast.error('Camera access is required to play.');
            setIsStarting(false);
            return;
        }
        try {
            const response = await api.startGame(30);
            endingRef.current = false;
            setResult(null);
            setHint('');
            setGameState({
                ...INITIAL_STATE,
                isActive: true,
                gameId: response.gameId,
                currentChallenge: response.currentChallenge,
                timeLeft: response.duration,
            });
            toast.success('Game started! Sign the word shown.');
        } catch (error: any) {
            stopCamera();
            toast.error(error.message || 'Failed to start game');
        } finally {
            setIsStarting(false);
        }
    };

    // Attach the stream once the <video> element is rendered
    useEffect(() => {
        if (gameState.isActive && videoRef.current && streamRef.current && videoRef.current.srcObject !== streamRef.current) {
            videoRef.current.srcObject = streamRef.current;
        }
    }, [gameState.isActive]);

    const endGame = async () => {
        if (endingRef.current) return;
        endingRef.current = true;
        if (loopRef.current) clearTimeout(loopRef.current);
        stopCamera();
        const gameId = gameStateRef.current.gameId;
        setGameState(prev => ({ ...prev, isActive: false, isGameOver: true, timeLeft: 0 }));
        if (!gameId) return;
        try {
            // Finalizes the game on the server (XP, history, achievements)
            setResult(await api.getGameResult(gameId));
        } catch (error: any) {
            toast.error(error.message || 'Could not save your game');
        }
    };

    // Countdown (display only; the server is authoritative)
    useEffect(() => {
        if (!gameState.isActive) return;
        if (gameState.timeLeft <= 0) {
            endGame();
            return;
        }
        const timer = setTimeout(() => {
            setGameState(prev => ({ ...prev, timeLeft: Math.max(0, prev.timeLeft - 1) }));
        }, 1000);
        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gameState.isActive, gameState.timeLeft]);

    const processFrame = async () => {
        const current = gameStateRef.current;
        const video = videoRef.current;
        if (!current.isActive || !current.gameId || endingRef.current) return;

        if (video && video.readyState >= 2 && video.videoWidth) {
            const canvas = canvasRef.current ?? (canvasRef.current = document.createElement('canvas'));
            canvas.width = 480;
            canvas.height = Math.round(480 * video.videoHeight / video.videoWidth);
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                try {
                    const response = await api.gameAttempt(current.gameId, canvas.toDataURL('image/jpeg', 0.6));
                    setHint(statusHint(response.buffer_status || ''));
                    setGameState(prev => ({
                        ...prev,
                        currentChallenge: response.currentChallenge,
                        score: response.score,
                        streak: response.streak,
                        bestStreak: Math.max(prev.bestStreak, response.streak),
                        multiplier: response.multiplier,
                        wordsCompleted: response.wordsCompleted,
                        timeLeft: Math.ceil(response.timeRemaining),
                    }));
                    if (response.correct) {
                        gsap.fromTo('.challenge-card',
                            { scale: 1.1, backgroundColor: 'rgba(34, 197, 94, 0.2)' },
                            { scale: 1, backgroundColor: 'transparent', duration: 0.5 }
                        );
                        toast.success(`Correct! +${response.score - current.score} points`, { position: 'top-center' });
                    }
                    if (!response.isActive) {
                        endGame();
                        return;
                    }
                } catch (e: any) {
                    if (e?.status === 409) {
                        endGame();
                        return;
                    }
                }
            }
        }
        if (gameStateRef.current.isActive && !endingRef.current) {
            loopRef.current = setTimeout(processFrame, FRAME_INTERVAL_MS);
        }
    };

    useEffect(() => {
        if (gameState.isActive) {
            loopRef.current = setTimeout(processFrame, FRAME_INTERVAL_MS);
        }
        return () => {
            if (loopRef.current) clearTimeout(loopRef.current);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [gameState.isActive, gameState.gameId]);

    return (
        <div className="min-h-screen p-6 md:p-12 overflow-hidden flex flex-col items-center">
            <div className="max-w-4xl w-full">
                <div className="game-header flex justify-between items-center mb-12">
                    <div>
                        <h1 className="text-4xl font-black bg-gradient-to-r from-orange-400 to-pink-600 bg-clip-text text-transparent italic">
                            ISL QUIZ RUSH
                        </h1>
                        <p className="text-sm font-bold text-gray-500 tracking-widest uppercase">Test your signs under pressure</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="bg-white dark:bg-gray-800 px-6 py-2 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 flex items-center gap-3">
                            <Timer className={`w-6 h-6 ${gameState.timeLeft < 10 ? 'text-red-500 animate-pulse' : 'text-gray-400'}`} />
                            <span className="text-2xl font-black">{gameState.timeLeft}s</span>
                        </div>
                        <div className="bg-[#105F68] px-6 py-2 rounded-2xl shadow-lg text-white flex items-center gap-3">
                            <Zap className="w-6 h-6 text-yellow-400 fill-current" />
                            <span className="text-2xl font-black">{gameState.score}</span>
                        </div>
                    </div>
                </div>

                {!gameState.isActive && !gameState.isGameOver ? (
                    <div className="flex flex-col items-center justify-center h-[500px] bg-white dark:bg-gray-800 rounded-[40px] shadow-2xl border-4 border-dashed border-gray-200 dark:border-gray-700 p-12 text-center">
                        <div className="w-32 h-32 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center mb-8">
                            <Trophy className="w-16 h-16 text-orange-500" />
                        </div>
                        <h2 className="text-3xl font-black mb-4">Ready for the Challenge?</h2>
                        <p className="text-gray-500 dark:text-gray-400 max-w-sm mb-12 italic">
                            You&apos;ll get a series of signs to perform. Each correct sign increases your streak and multiplier!
                        </p>
                        <button
                            onClick={startGame}
                            disabled={isStarting}
                            className="disabled:opacity-60 px-12 py-5 bg-gradient-to-r from-orange-500 to-pink-600 text-white rounded-[24px] font-black text-xl shadow-2xl hover:scale-105 transition-all flex items-center gap-3"
                        >
                            <Play className="w-6 h-6 fill-current" /> START RUSH
                        </button>
                    </div>
                ) : gameState.isGameOver ? (
                    <div className="flex flex-col items-center justify-center h-[500px] bg-white dark:bg-gray-800 rounded-[40px] shadow-2xl p-12 text-center">
                        <Trophy className="w-24 h-24 text-yellow-500 mb-6 drop-shadow-lg" />
                        <h2 className="text-4xl font-black mb-2 tracking-tight">Final Score: {result?.score ?? gameState.score}</h2>
                        <p className="text-lg text-gray-500 mb-2">Completed {result?.wordsCompleted ?? gameState.wordsCompleted} signs</p>
                        {result ? (
                            <>
                                <p className="text-sm text-gray-500 mb-4">
                                    Accuracy {result.accuracy}% · Best streak {result.streak_best}
                                </p>
                                <div className="flex flex-wrap justify-center gap-2 mb-8">
                                    {result.badges.map((b) => (
                                        <span key={b} className="px-3 py-1.5 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-600 text-sm font-bold">{b}</span>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <p className="text-sm text-gray-400 mb-8">Saving your results...</p>
                        )}
                        <div className="flex gap-4">
                            <button onClick={() => router.push('/dashboard')} className="px-8 py-4 bg-gray-100 dark:bg-gray-700 rounded-2xl font-bold flex items-center gap-2">
                                <Home className="w-5 h-5" /> Dashboard
                            </button>
                            <button onClick={startGame} disabled={isStarting} className="disabled:opacity-60 px-8 py-4 bg-[#105F68] text-white rounded-2xl font-bold flex items-center gap-2 shadow-xl hover:scale-105 transition-all">
                                <RefreshCw className="w-5 h-5" /> Play Again
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="relative group">
                        <div className="camera-view aspect-video bg-black rounded-[40px] overflow-hidden shadow-2xl border-8 border-white dark:border-gray-800 relative">
                            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />

                            <div className="absolute inset-x-0 bottom-0 p-8 bg-gradient-to-t from-black/80 to-transparent">
                                <div className="challenge-card p-6 bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl text-center">
                                    <p className="text-xs font-bold text-white/60 uppercase tracking-widest mb-1">Current Challenge</p>
                                    <h2 className="text-6xl font-black text-white tracking-tight mb-2">{gameState.currentChallenge}</h2>
                                    <p className="text-sm text-white/70 h-5 mb-2">{hint}</p>
                                    <div className="flex justify-center gap-4">
                                        <div className="flex items-center gap-2 bg-white/20 px-4 py-1.5 rounded-full text-white text-sm font-bold">
                                            <Zap className="w-4 h-4 text-yellow-400 fill-current" />
                                            Streak x{gameState.streak}
                                        </div>
                                        <div className="flex items-center gap-2 bg-white/20 px-4 py-1.5 rounded-full text-white text-sm font-bold">
                                            <Target className="w-4 h-4 text-green-400" />
                                            x{gameState.multiplier} Bonus
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Hint overlay */}
                        <div className="absolute top-1/2 -translate-y-1/2 -right-32 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <div className="w-24 h-24 bg-white/80 dark:bg-gray-800/80 backdrop-blur rounded-full flex items-center justify-center border-4 border-[#105F68] text-2xl font-bold text-[#105F68] animate-bounce">
                                🤟
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-3 gap-6 mt-12">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-lg text-center">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Best Streak</p>
                        <p className="text-2xl font-black text-orange-500">{gameState.bestStreak}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-lg text-center">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Multiplier</p>
                        <p className="text-2xl font-black text-pink-500">x{gameState.multiplier}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-lg text-center">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Signs Completed</p>
                        <p className="text-2xl font-black text-violet-500">{gameState.wordsCompleted}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
