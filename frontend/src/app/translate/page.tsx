"use client";

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Camera, CameraOff, RefreshCw, Layers, Brain, Zap, Info, History as HistoryIcon } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';

interface Landmark {
    x: number;
    y: number;
    z: number;
    visibility: number;
}

interface ARResponse {
    pose_landmarks: Landmark[];
    left_hand_landmarks: Landmark[];
    right_hand_landmarks: Landmark[];
    face_detected: boolean;
    prediction: string | null;
    confidence: number;
    gesture_hint: string;
    history: string[];
}

export default function ARRecognizePage() {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isActive, setIsActive] = useState(false);
    const [isARMode, setIsARMode] = useState(true);
    const [prediction, setPrediction] = useState<string | null>(null);
    const [confidence, setConfidence] = useState(0);
    const [hint, setHint] = useState('Position yourself in view to start');
    const [history, setHistory] = useState<string[]>([]);
    const [stats, setStats] = useState({ fps: 0, latency: 0 });
    const requestRef = useRef<number>();
    const lastTimeRef = useRef<number>(0);
    const lastSpokenRef = useRef<string>('');
    const lastPredictionRef = useRef<string | null>(null);

    useEffect(() => {
        gsap.fromTo('.camera-main', { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.8, ease: 'power3.out' });
    }, []);

    useEffect(() => {
        if (prediction && isActive && prediction !== lastSpokenRef.current && confidence > 0.7) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(prediction);
                utterance.rate = 1.0;
                utterance.pitch = 1.1;
                window.speechSynthesis.speak(utterance);
                lastSpokenRef.current = prediction;

                toast.info(`Speaking: ${prediction}`, { icon: '🔊', duration: 2000 });
            }
        }
        if (!prediction) lastSpokenRef.current = '';
    }, [prediction, isActive, confidence]);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setIsActive(true);
                toast.success('Camera initialized');
            }
        } catch (err) {
            toast.error('Failed to access camera. Please grant permissions.');
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
            tracks.forEach(track => track.stop());
            setIsActive(false);
            setPrediction(null);
            setHint('Camera stopped');
        }
    };

    const captureAndProcess = async () => {
        if (!isActive || !videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.drawImage(video, 0, 0, 640, 480);
        const frame = canvas.toDataURL('image/jpeg', 0.7);

        const startTime = performance.now();
        try {
            const data: ARResponse = await api.getARLandmarks(frame);
            const endTime = performance.now();

            setStats({
                latency: Math.round(endTime - startTime),
                fps: Math.round(1000 / (endTime - lastTimeRef.current))
            });
            lastTimeRef.current = endTime;

            setPrediction(data.prediction);
            setConfidence(data.confidence);
            setHistory(data.history || []);
            setHint(data.gesture_hint || (data.face_detected ? 'Listening for signs...' : 'Face not detected'));

            if (data.prediction && data.prediction !== lastPredictionRef.current) {
                lastPredictionRef.current = data.prediction;
                gsap.fromTo('.prediction-badge', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: 'back.out(2)' });
            }

            if (isARMode) {
                drawAROverlay(data);
            } else {
                clearCanvas();
            }
        } catch (error) {
            console.error(error);
        }

        if (isActive) {
            setTimeout(() => {
                requestRef.current = requestAnimationFrame(captureAndProcess);
            }, 50); // Small delay to avoid hammering the server
        }
    };

    useEffect(() => {
        if (isActive) {
            requestRef.current = requestAnimationFrame(captureAndProcess);
        } else {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        }
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [isActive, isARMode]);

    const clearCanvas = () => {
        const canvas = canvasRef.current;
        if (canvas) {
            const ctx = canvas.getContext('2d');
            if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    };

    const drawAROverlay = (data: ARResponse) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const { width, height } = canvas;

        // Draw Hands
        const drawHand = (landmarks: Landmark[], color: string) => {
            if (!landmarks.length) return;
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
            ctx.lineWidth = 3;

            // Draw connections
            const connections = [
                [0, 1, 2, 3, 4], // Thumb
                [0, 5, 6, 7, 8], // Index
                [0, 9, 10, 11, 12], // Middle
                [0, 13, 14, 15, 16], // Ring
                [0, 17, 18, 19, 20], // Pinky
                [5, 9, 13, 17], // Palm base
            ];

            connections.forEach(path => {
                ctx.beginPath();
                path.forEach((idx, i) => {
                    const pt = landmarks[idx];
                    if (i === 0) ctx.moveTo(pt.x * width, pt.y * height);
                    else ctx.lineTo(pt.x * width, pt.y * height);
                });
                ctx.stroke();
            });

            // Draw points
            landmarks.forEach(pt => {
                ctx.beginPath();
                ctx.arc(pt.x * width, pt.y * height, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        };

        drawHand(data.left_hand_landmarks, '#63C1BB');
        drawHand(data.right_hand_landmarks, '#C8E6E2');

        // Draw Pose Skeleton (simplified)
        if (data.pose_landmarks.length) {
            ctx.strokeStyle = 'rgba(16, 95, 104, 0.5)';
            ctx.lineWidth = 2;
            const poseIdx = [11, 12, 13, 14, 15, 16, 23, 24]; // Shoulders, elbows, wrists, hips

            // Draw shoulder to shoulder
            ctx.beginPath();
            ctx.moveTo(data.pose_landmarks[11].x * width, data.pose_landmarks[11].y * height);
            ctx.lineTo(data.pose_landmarks[12].x * width, data.pose_landmarks[12].y * height);
            ctx.stroke();

            // Draw arms
            [[11, 13, 15], [12, 14, 16]].forEach(arm => {
                ctx.beginPath();
                arm.forEach((idx, i) => {
                    const pt = data.pose_landmarks[idx];
                    if (i === 0) ctx.moveTo(pt.x * width, pt.y * height);
                    else ctx.lineTo(pt.x * width, pt.y * height);
                });
                ctx.stroke();
            });
        }
    };

    return (
        <div className="min-h-screen p-6 md:p-12 overflow-hidden">
            <div className="max-w-7xl mx-auto flex flex-col h-full">
                {/* Header */}
                <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[#105F68] to-[#3A9295] bg-clip-text text-transparent">
                            SignVista: AR Translate
                        </h1>
                        <p className="text-gray-600 dark:text-gray-400 mt-2">
                            Instant ISL recognition with augmented reality overlays and voice feedback
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => setIsARMode(!isARMode)}
                            className={`px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all ${isARMode ? 'bg-[#105F68] text-white shadow-lg' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}
                        >
                            <Layers className="w-4 h-4" />
                            AR {isARMode ? 'On' : 'Off'}
                        </button>
                        <button
                            onClick={isActive ? stopCamera : startCamera}
                            className={`px-6 py-2 rounded-xl font-bold flex items-center gap-2 transition-all shadow-xl hover:scale-105 ${isActive ? 'bg-red-500 text-white' : 'bg-[#3A9295] text-white'}`}
                        >
                            {isActive ? <CameraOff className="w-5 h-5" /> : <Camera className="w-5 h-5" />}
                            {isActive ? 'Stop' : 'Start Camera'}
                        </button>
                    </div>
                </div>

                <div className="grid lg:grid-cols-4 gap-8 flex-1">
                    {/* Main View */}
                    <div className="lg:col-span-3 space-y-6">
                        <div className="camera-main relative aspect-video bg-black rounded-[32px] overflow-hidden shadow-2xl border-4 border-white dark:border-gray-800">
                            <video
                                ref={videoRef}
                                autoPlay
                                playsInline
                                muted
                                className="w-full h-full object-cover scale-x-[-1]"
                            />
                            <canvas
                                ref={canvasRef}
                                width={640}
                                height={480}
                                className="absolute inset-0 w-full h-full pointer-events-none scale-x-[-1]"
                            />

                            {/* UI Overlays on Camera */}
                            <div className="absolute top-6 left-6 flex gap-2">
                                <div className="bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full text-white text-xs flex items-center gap-2 border border-white/20">
                                    <Zap className="w-3 h-3 text-yellow-400 fill-current" />
                                    {stats.latency}ms
                                </div>
                                <div className="bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full text-white text-xs flex items-center gap-2 border border-white/20">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    Live
                                </div>
                            </div>

                            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-md px-6">
                                <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 text-white shadow-2xl relative overflow-hidden">
                                    {hint && hint !== 'Listening for signs...' && (
                                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-yellow-400 to-orange-500 animate-pulse" />
                                    )}
                                    {prediction ? (
                                        <div className="prediction-badge animate-in fade-in zoom-in duration-300">
                                            <p className="text-sm opacity-60 uppercase tracking-widest mb-1">Detected Word</p>
                                            <h2 className="text-5xl font-black mb-2 tracking-tight">{prediction}</h2>
                                            <div className="flex items-center justify-center gap-2">
                                                <div className="w-32 h-1.5 bg-white/20 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full transition-all duration-300 ${confidence > 0.7 ? 'bg-[#63C1BB]' : 'bg-yellow-500'}`}
                                                        style={{ width: `${confidence * 100}%` }}
                                                    />
                                                </div>
                                                <span className="text-xs font-bold">{Math.round(confidence * 100)}%</span>
                                            </div>
                                            {hint && hint !== 'Listening for signs...' && (
                                                <p className="mt-3 text-sm font-bold text-yellow-400 bg-yellow-400/10 py-1 rounded-lg border border-yellow-400/20">
                                                    ⚠️ {hint}
                                                </p>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center gap-3">
                                            <RefreshCw className={`w-8 h-8 opacity-40 ${isActive ? 'animate-spin' : ''}`} />
                                            <p className="text-lg font-medium opacity-80">{hint}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Hint Card */}
                        <div className="bg-gradient-to-r from-[#C8E6E2] to-[#BFCFBB] p-4 rounded-2xl flex items-center gap-4 border border-white/20">
                            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-md">
                                <Info className="w-5 h-5 text-[#105F68]" />
                            </div>
                            <p className="text-sm text-[#105F68] font-medium">
                                Tip: Maintain a distance of about 1-2 meters and ensure good lighting for better accuracy.
                            </p>
                        </div>
                    </div>

                    {/* Stats & Tools */}
                    <div className="space-y-6">
                        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-700">
                            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                                <Brain className="w-6 h-6 text-[#105F68]" /> Engine Stats
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
                                    <span className="text-sm text-gray-500">Latency</span>
                                    <span className="font-bold text-[#105F68]">{stats.latency} ms</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
                                    <span className="text-sm text-gray-500">FPS</span>
                                    <span className="font-bold text-[#105F68]">{stats.fps}</span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
                                    <span className="text-sm text-gray-500">Accuracy</span>
                                    <span className="font-bold text-[#105F68]">{Math.round(confidence * 100)}%</span>
                                </div>
                            </div>
                        </div>

                        {/* Multi-Word History */}
                        <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-xl border border-gray-100 dark:border-gray-700">
                            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                                <HistoryIcon className="w-6 h-6 text-[#105F68]" /> Translation History
                            </h3>
                            <div className="space-y-3">
                                {history.length > 0 ? history.map((word, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-xl border-l-4 border-[#105F68] animate-in slide-in-from-left duration-300" style={{ animationDelay: `${i * 0.1}s` }}>
                                        <span className="font-bold text-gray-800 dark:text-gray-200 uppercase tracking-wide">{word}</span>
                                        <span className="text-[10px] text-gray-400">{i === 0 ? 'Latest' : `${i} predictions ago`}</span>
                                    </div>
                                )) : (
                                    <div className="text-center py-8">
                                        <p className="text-sm text-gray-400">No history yet</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="bg-[#105F68] rounded-3xl p-8 text-white shadow-xl relative overflow-hidden group">
                            <div className="absolute -right-4 -top-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                                <Zap className="w-32 h-32" />
                            </div>
                            <h3 className="text-xl font-bold mb-4 relative z-10">Smart Feedback</h3>
                            <p className="text-sm opacity-80 leading-relaxed mb-6 relative z-10">
                                Our AI provides real-time tips to help you form the correct signs. Watch the gesture hints below the prediction.
                            </p>
                            <button className="w-full py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl text-sm font-bold transition-all">
                                Learn More
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
