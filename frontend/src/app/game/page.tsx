"use client";

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Trophy, Timer, Zap, Target, RefreshCw, Play, Home, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface GameState {
    isActive: boolean;
    gameId: string | null;
    currentChallenge: string;
    score: number;
    streak: number;
    multiplier: number;
    timeLeft: number;
    wordsCompleted: number;
    isGameOver: boolean;
}

export default function GamePage() {
    const [gameState, setGameState] = useState<GameState>({
        isActive: false,
        gameId: null,
        currentChallenge: '',
        score: 0,
        streak: 0,
        multiplier: 1,
        timeLeft: 30,
        wordsCompleted: 0,
        isGameOver: false,
    });

    const videoRef = useRef<HTMLVideoElement>(null);
    const [isCameraActive, setIsCameraActive] = useState(false);
    const requestRef = useRef<number>();

    useEffect(() => {
        gsap.fromTo('.game-header', { y: -20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8 });
    }, []);

    const startGame = async () => {
        try {
            const response = await api.post('/game/start', { sessionId: api.getSessionId(), duration: 30 });
            setGameState({
                isActive: true,
                gameId: response.gameId,
                currentChallenge: response.currentChallenge,
                score: 0,
                streak: 0,
                multiplier: 1,
                timeLeft: response.duration,
                wordsCompleted: 0,
                isGameOver: false,
            });
            await startCamera();
            toast.success('Game Started! Sign the word below.');
        } catch (error) {
            toast.error('Failed to start game');
        }
    };

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setIsCameraActive(true);
            }
        } catch (err) {
            toast.error('Camera access denied');
        }
    };

    useEffect(() => {
        let timer: any;
        if (gameState.isActive && gameState.timeLeft > 0) {
            timer = setInterval(() => {
                setGameState(prev => ({
                    ...prev,
                    timeLeft: prev.timeLeft - 1
                }));
            }, 1000);
        } else if (gameState.timeLeft === 0 && gameState.isActive) {
            endGame();
        }
        return () => clearInterval(timer);
    }, [gameState.isActive, gameState.timeLeft]);

    const endGame = () => {
        setGameState(prev => ({ ...prev, isActive: false, isGameOver: true }));
        setIsCameraActive(false);
        if (videoRef.current && videoRef.current.srcObject) {
            (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
        }
        toast.success('Game Over! Check your score.');
    };

    const processFrame = async () => {
        if (!gameState.isActive || !isCameraActive || !videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = 300;
        canvas.height = 225;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(videoRef.current, 0, 0, 300, 225);
        const frame = canvas.toDataURL('image/jpeg', 0.5);

        try {
            const response = await api.post('/game/attempt', {
                sessionId: api.getSessionId(),
                gameId: gameState.gameId,
                frame: frame
            });

            if (response.correct) {
                setGameState(prev => ({
                    ...prev,
                    currentChallenge: response.currentChallenge,
                    score: response.score,
                    streak: response.streak,
                    multiplier: response.multiplier,
                    wordsCompleted: response.wordsCompleted
                }));

                gsap.fromTo('.challenge-card',
                    { scale: 1.1, backgroundColor: 'rgba(34, 197, 94, 0.2)' },
                    { scale: 1, backgroundColor: 'transparent', duration: 0.5 }
                );
                toast.success(`Correct! +${response.score - gameState.score} XP`, { position: 'top-center' });
            }
        } catch (e) {
            console.error(e);
        }

        if (gameState.isActive) {
            requestRef.current = requestAnimationFrame(() => setTimeout(processFrame, 500));
        }
    };

    useEffect(() => {
        if (gameState.isActive && isCameraActive) {
            requestRef.current = requestAnimationFrame(processFrame);
        }
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [gameState.isActive, isCameraActive]);

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
                            You'll get a series of words to sign. Each correct sign increases your streak and multiplier!
                        </p>
                        <button
                            onClick={startGame}
                            className="px-12 py-5 bg-gradient-to-r from-orange-500 to-pink-600 text-white rounded-[24px] font-black text-xl shadow-2xl hover:scale-105 transition-all flex items-center gap-3"
                        >
                            <Play className="w-6 h-6 fill-current" /> START RUSH
                        </button>
                    </div>
                ) : gameState.isGameOver ? (
                    <div className="flex flex-col items-center justify-center h-[500px] bg-white dark:bg-gray-800 rounded-[40px] shadow-2xl p-12 text-center">
                        <Trophy className="w-24 h-24 text-yellow-500 mb-6 drop-shadow-lg" />
                        <h2 className="text-4xl font-black mb-2 tracking-tight">Final Score: {gameState.score}</h2>
                        <p className="text-lg text-gray-500 mb-8">Completed {gameState.wordsCompleted} signs</p>
                        <div className="flex gap-4">
                            <button onClick={() => window.location.href = '/dashboard'} className="px-8 py-4 bg-gray-100 dark:bg-gray-700 rounded-2xl font-bold flex items-center gap-2">
                                <Home className="w-5 h-5" /> Dashboard
                            </button>
                            <button onClick={startGame} className="px-8 py-4 bg-[#105F68] text-white rounded-2xl font-bold flex items-center gap-2 shadow-xl hover:scale-105 transition-all">
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
                                    <h2 className="text-6xl font-black text-white tracking-tight mb-4">{gameState.currentChallenge}</h2>
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
                        <p className="text-2xl font-black text-orange-500">{gameState.streak}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-lg text-center">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">XP Multiplier</p>
                        <p className="text-2xl font-black text-pink-500">x{gameState.multiplier}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-100 dark:border-gray-700 shadow-lg text-center">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Total Mastered</p>
                        <p className="text-2xl font-black text-violet-500">{gameState.wordsCompleted}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
