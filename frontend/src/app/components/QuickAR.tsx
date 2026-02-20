"use client";

import { useState, useEffect, useRef } from 'react';
import { Zap, RefreshCw, Camera, CameraOff } from 'lucide-react';
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
}

export function QuickAR() {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isActive, setIsActive] = useState(false);
    const [prediction, setPrediction] = useState<string | null>(null);
    const [confidence, setConfidence] = useState(0);
    const [stats, setStats] = useState({ latency: 0 });
    const requestRef = useRef<number>();
    const lastTimeRef = useRef<number>(0);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setIsActive(true);
            }
        } catch (err) {
            console.error('Failed to access camera:', err);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
            tracks.forEach(track => track.stop());
            setIsActive(false);
            setPrediction(null);
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
        const frame = canvas.toDataURL('image/jpeg', 0.6);

        const startTime = performance.now();
        try {
            const data: ARResponse = await api.getARLandmarks(frame);
            const endTime = performance.now();

            setStats({ latency: Math.round(endTime - startTime) });
            setPrediction(data.prediction);
            setConfidence(data.confidence);

            drawAROverlay(data);
        } catch (error) {
            console.error(error);
        }

        if (isActive) {
            setTimeout(() => {
                requestRef.current = requestAnimationFrame(captureAndProcess);
            }, 100);
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
    }, [isActive]);

    const drawAROverlay = (data: ARResponse) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const { width, height } = canvas;

        const drawHand = (landmarks: Landmark[], color: string) => {
            if (!landmarks || !landmarks.length) return;
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
            ctx.lineWidth = 2;

            const connections = [
                [0, 1, 2, 3, 4], [0, 5, 6, 7, 8], [0, 9, 10, 11, 12],
                [0, 13, 14, 15, 16], [0, 17, 18, 19, 20], [5, 9, 13, 17],
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

            landmarks.forEach(pt => {
                ctx.beginPath();
                ctx.arc(pt.x * width, pt.y * height, 2, 0, Math.PI * 2);
                ctx.fill();
            });
        };

        drawHand(data.left_hand_landmarks, '#63C1BB');
        drawHand(data.right_hand_landmarks, '#C8E6E2');
    };

    return (
        <div className="relative w-full h-full bg-black rounded-3xl overflow-hidden group shadow-2xl">
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

            {!isActive ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/60 backdrop-blur-sm">
                    <button
                        onClick={startCamera}
                        className="p-6 bg-white rounded-full shadow-2xl transform transition hover:scale-110 active:scale-95"
                    >
                        <Camera className="w-8 h-8 text-[#105F68]" />
                    </button>
                    <p className="mt-4 text-white font-bold opacity-80 letter-spacing-wide">START REAL-TIME TRANSLATION</p>
                </div>
            ) : (
                <>
                    <div className="absolute top-4 left-4 flex gap-2">
                        <div className="bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-[10px] text-white flex items-center gap-1.5 border border-white/20">
                            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                            LIVE
                        </div>
                        <div className="bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-[10px] text-white flex items-center gap-1.5 border border-white/20">
                            <Zap className="w-2.5 h-2.5 text-yellow-400" />
                            {stats.latency}ms
                        </div>
                    </div>

                    <button
                        onClick={stopCamera}
                        className="absolute top-4 right-4 p-2 bg-black/40 backdrop-blur-md rounded-full text-white/60 hover:text-red-400 transition-colors border border-white/20"
                    >
                        <CameraOff className="w-4 h-4" />
                    </button>

                    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-[85%]">
                        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-4 text-center text-white shadow-2xl">
                            {prediction ? (
                                <div className="animate-in fade-in zoom-in duration-300">
                                    <h2 className="text-3xl font-black mb-1">{prediction}</h2>
                                    <div className="flex items-center justify-center gap-2">
                                        <div className="w-20 h-1 bg-white/20 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-[#63C1BB] transition-all duration-300"
                                                style={{ width: `${confidence * 100}%` }}
                                            />
                                        </div>
                                        <span className="text-[10px] font-bold opacity-60">{Math.round(confidence * 100)}%</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center justify-center gap-2 opacity-60">
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                    <p className="text-sm font-medium">Scanning for signs...</p>
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
