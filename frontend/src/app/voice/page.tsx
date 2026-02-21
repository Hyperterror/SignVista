"use client";

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Mic, MicOff, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { api, BACKEND_ORIGIN } from '../utils/api';

interface SignWord {
    word: string;
    display_name: string;
    found: boolean;
    gif_url: string;
    description: string;
    duration_ms: number;
}

export default function VoiceToSignPage() {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [outputSigns, setOutputSigns] = useState<SignWord[]>([]);
    const [waveformActive, setWaveformActive] = useState(false);
    const micRef = useRef<HTMLDivElement>(null);
    const glowRef = useRef<HTMLDivElement>(null);
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        gsap.fromTo('.voice-container', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.8, ease: 'back.out(1.7)' });

        // Initialize Speech Recognition
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.interimResults = true;
            recognitionRef.current.lang = 'en-IN'; // Default to Indian English

            recognitionRef.current.onresult = (event: any) => {
                let currentTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    currentTranscript += event.results[i][0].transcript;
                }
                setTranscript(currentTranscript);
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);
                toast.error('Speech recognition failed. Please check your microphone.');
                setIsRecording(false);
                setWaveformActive(false);
            };

            recognitionRef.current.onend = () => {
                setIsRecording(false);
                setWaveformActive(false);
            };
        } else {
            toast.error('Web Speech API is not supported in this browser.');
        }

        return () => {
            if (recognitionRef.current) recognitionRef.current.stop();
        };
    }, []);

    useEffect(() => {
        if (isRecording && glowRef.current) {
            gsap.to(glowRef.current, { opacity: 1, scale: 1.1, duration: 1, ease: 'power1.inOut', yoyo: true, repeat: -1 });
            const interval = setInterval(() => createParticle(), 200);
            return () => clearInterval(interval);
        } else if (glowRef.current) {
            gsap.to(glowRef.current, { opacity: 0, scale: 1, duration: 0.5 });
        }
    }, [isRecording]);

    const createParticle = () => {
        if (!micRef.current) return;
        const particle = document.createElement('div');
        particle.className = 'absolute w-2 h-2 rounded-full';
        particle.style.backgroundColor = '#63C1BB';
        const angle = Math.random() * Math.PI * 2;
        const distance = 80 + Math.random() * 40;
        const startX = Math.cos(angle) * 60;
        const startY = Math.sin(angle) * 60;
        particle.style.left = `calc(50% + ${startX}px)`;
        particle.style.top = `calc(50% + ${startY}px)`;
        micRef.current.appendChild(particle);
        gsap.fromTo(particle,
            { x: 0, y: 0, opacity: 1, scale: 1 },
            { x: Math.cos(angle) * distance - startX, y: Math.sin(angle) * distance - startY, opacity: 0, scale: 0, duration: 1.5, ease: 'power2.out', onComplete: () => particle.remove() }
        );
    };

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const startRecording = () => {
        if (!recognitionRef.current) {
            toast.error('Voice recognition not initialized');
            return;
        }
        setTranscript('');
        setOutputSigns([]);
        setIsRecording(true);
        setWaveformActive(true);
        recognitionRef.current.start();
        toast.info('Listening...');
    };

    const stopRecording = async () => {
        setIsRecording(false);
        setWaveformActive(false);
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }

        if (transcript.trim()) {
            try {
                const response = await api.translateText(transcript);
                setOutputSigns(response.words);

                if (response.matched_words > 0) {
                    toast.success(`Found ${response.matched_words} signs!`);

                    // TTS for translated words
                    if ('speechSynthesis' in window) {
                        const textToSpeak = response.words
                            .filter((s: any) => s.found)
                            .map((s: any) => s.display_name)
                            .join(', ');
                        if (textToSpeak) {
                            const utterance = new SpeechSynthesisUtterance(textToSpeak);
                            utterance.rate = 0.9;
                            window.speechSynthesis.speak(utterance);
                        }
                    }

                    response.words.forEach((_: any, index: number) => {
                        gsap.fromTo(`.voice-sign-${index}`, { scale: 0, y: 50, opacity: 0 }, { scale: 1, y: 0, opacity: 1, duration: 0.5, delay: index * 0.1, ease: 'back.out(2)' });
                    });
                } else {
                    toast.warning('No matching ISL signs found');
                }
            } catch (error) {
                toast.error('Translation failed');
            }
        }
    };

    const clearAll = () => {
        setTranscript('');
        setOutputSigns([]);
        gsap.fromTo('.results-container', { scale: 1 }, { scale: 0.95, duration: 0.1, yoyo: true, repeat: 1 });
    };

    return (
        <div className="min-h-screen p-6 md:p-12">
            <div className="max-w-5xl mx-auto">
                <div className="mb-12">
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-clip-text text-transparent"
                        style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #3A9295)' }}
                    >
                        SignVista Voice
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400">
                        Speak naturally and watch your words transform into ISL gestures
                    </p>
                </div>

                <div className="voice-container mb-12">
                    <div className="relative rounded-3xl p-12 border-2 shadow-2xl"
                        style={{ background: 'linear-gradient(135deg, #ffffff, rgba(200, 230, 226, 0.15))', borderColor: '#9ED5D1' }}
                    >
                        <div ref={glowRef} className="absolute inset-0 rounded-3xl opacity-0 blur-xl -z-10"
                            style={{ background: 'linear-gradient(135deg, #3A9295, #63C1BB, #738A6E)' }}
                        />

                        <div className="flex flex-col items-center justify-center">
                            <div ref={micRef} className="relative mb-8">
                                <button
                                    onClick={toggleRecording}
                                    className="relative w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl"
                                    style={isRecording
                                        ? { background: 'linear-gradient(135deg, #ef4444, #ec4899)' }
                                        : { background: 'linear-gradient(135deg, #344C3D, #105F68)' }
                                    }
                                >
                                    {isRecording ? <MicOff className="w-12 h-12 text-white" /> : <Mic className="w-12 h-12 text-white" />}
                                </button>
                                {isRecording && (
                                    <>
                                        <div className="absolute inset-0 rounded-full border-4 border-red-400 animate-ping opacity-75" />
                                        <div className="absolute inset-0 rounded-full border-4 border-pink-400 animate-ping opacity-50" style={{ animationDelay: '0.3s' }} />
                                    </>
                                )}
                            </div>

                            <div className="text-center mb-6">
                                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                                    {isRecording ? 'Listening...' : 'Tap to Start Recording'}
                                </p>
                                <p className="text-gray-600 dark:text-gray-400">
                                    {isRecording ? 'Speak clearly into your microphone' : "We'll convert your speech to ISL"}
                                </p>
                            </div>

                            {waveformActive && (
                                <div className="flex gap-2 h-16 items-center justify-center">
                                    {Array.from({ length: 20 }).map((_, i) => (
                                        <div key={i} className="w-1 rounded-full animate-waveform"
                                            style={{ background: 'linear-gradient(to top, #344C3D, #3A9295)', animationDelay: `${i * 0.05}s`, height: '20%' }}
                                        />
                                    ))}
                                </div>
                            )}

                            {transcript && (
                                <div className="mt-8 w-full max-w-2xl p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg">
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Transcript:</h3>
                                        {!isRecording && (
                                            <button onClick={clearAll} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-300">
                                                <Trash2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                            </button>
                                        )}
                                    </div>
                                    <p className="text-lg text-gray-700 dark:text-gray-300 italic">"{transcript}"</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {outputSigns.length > 0 && (
                    <div className="results-container">
                        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border border-gray-200 dark:border-gray-700">
                            <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-gray-100">ISL Translation</h2>
                            <div className="flex flex-wrap gap-6 justify-center mb-8">
                                {outputSigns.map((sign, index) => (
                                    <div key={index} className={`voice-sign-${index} relative group w-full max-w-[180px]`}>
                                        <div className="relative aspect-video rounded-2xl overflow-hidden bg-white dark:bg-gray-800 shadow-lg border border-gray-100 dark:border-gray-700 hover:shadow-2xl transition-all duration-300">
                                            {sign.found ? (
                                                <img
                                                    src={`${BACKEND_ORIGIN}${sign.gif_url}`}
                                                    alt={sign.display_name}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex flex-col items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
                                                    <span className="text-xs text-gray-400">"{sign.word}"</span>
                                                    <span className="text-[10px] text-gray-300">No Sign Found</span>
                                                </div>
                                            )}
                                        </div>
                                        <div className="mt-2 text-center">
                                            <span className="text-sm font-bold text-[#105F68] dark:text-[#63C1BB]">{sign.display_name}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                                {outputSigns.filter(s => s.found).length} / {outputSigns.length} signs matched
                            </div>
                        </div>
                    </div>
                )}

                {/* Info Cards */}
                <div className="grid md:grid-cols-3 gap-6 mt-12">
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: '#C8E6E2', borderColor: '#9ED5D1' }}>
                        <div className="text-3xl mb-3">🎤</div>
                        <h3 className="font-semibold mb-2" style={{ color: '#105F68' }}>Clear Speech</h3>
                        <p className="text-sm" style={{ color: '#3A9295' }}>Speak clearly and at a moderate pace for best results</p>
                    </div>

                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: '#BFCFBB', borderColor: '#8EA58C' }}>
                        <div className="text-3xl mb-3">🔊</div>
                        <h3 className="font-semibold mb-2" style={{ color: '#344C3D' }}>Quiet Environment</h3>
                        <p className="text-sm" style={{ color: '#738A6E' }}>Record in a quiet space to minimize background noise</p>
                    </div>

                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'rgba(158, 213, 209, 0.3)', borderColor: '#63C1BB' }}>
                        <div className="text-3xl mb-3">✨</div>
                        <h3 className="font-semibold mb-2" style={{ color: '#105F68' }}>AI Powered</h3>
                        <p className="text-sm" style={{ color: '#3A9295' }}>Advanced AI ensures accurate voice-to-sign conversion</p>
                    </div>
                </div>
            </div>

            <style>{`
        @keyframes waveform {
          0%, 100% { height: 20%; }
          50% { height: 100%; }
        }
        .animate-waveform {
          animation: waveform 1s ease-in-out infinite;
        }
      `}</style>
        </div>
    );
}
