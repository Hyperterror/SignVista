"use client";

import { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Type, Mic, MicOff, Send, Trash2, X } from 'lucide-react';
import { toast } from 'sonner';
import { api, BACKEND_ORIGIN } from '../../utils/api';

interface SignWord {
    word: string;
    display_name: string;
    found: boolean;
    gif_url: string;
    description: string;
    duration_ms: number;
}

export default function SignToolbox({ onClose }: { onClose?: () => void }) {
    const [mode, setMode] = useState<'text' | 'voice'>('text');
    const [inputText, setInputText] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [outputSigns, setOutputSigns] = useState<SignWord[]>([]);
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        // Initialize Speech Recognition
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = true;
            recognitionRef.current.interimResults = true;
            recognitionRef.current.lang = 'en-IN';

            recognitionRef.current.onresult = (event: any) => {
                let currentTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    currentTranscript += event.results[i][0].transcript;
                }
                setTranscript(currentTranscript);
            };

            recognitionRef.current.onend = () => setIsRecording(false);
        }
    }, []);

    const handleTextConvert = async () => {
        if (!inputText.trim()) return;
        setIsProcessing(true);
        try {
            const response = await api.translateText(inputText);
            setOutputSigns(response.words);
        } catch (error) {
            toast.error('Sign conversion failed');
        } finally {
            setIsProcessing(false);
        }
    };

    const toggleRecording = () => {
        if (isRecording) {
            recognitionRef.current?.stop();
            handleVoiceConvert();
        } else {
            setTranscript('');
            setOutputSigns([]);
            setIsRecording(true);
            recognitionRef.current?.start();
        }
    };

    const handleVoiceConvert = async () => {
        if (!transcript.trim()) return;
        setIsProcessing(true);
        try {
            const response = await api.translateText(transcript);
            setOutputSigns(response.words);
        } catch (error) {
            toast.error('Voice conversion failed');
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-l border-gray-100 dark:border-gray-800 animate-in slide-in-from-right duration-500">
            <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/30">
                <h3 className="text-lg font-black text-[#105F68] dark:text-[#63C1BB] flex items-center gap-2">
                    <Type className="w-5 h-5" /> Sign Toolbox
                </h3>
                {onClose && (
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors">
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                )}
            </div>

            <div className="p-6 space-y-6 flex-1 overflow-y-auto custom-scrollbar">
                {/* Mode Selector */}
                <div className="flex p-1 bg-gray-100 dark:bg-gray-800 rounded-xl">
                    <button
                        onClick={() => setMode('text')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${mode === 'text' ? 'bg-white dark:bg-gray-700 text-[#105F68] shadow-sm' : 'text-gray-500'}`}
                    >
                        <Type className="w-3.5 h-3.5" /> Text
                    </button>
                    <button
                        onClick={() => setMode('voice')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${mode === 'voice' ? 'bg-white dark:bg-gray-700 text-[#105F68] shadow-sm' : 'text-gray-500'}`}
                    >
                        <Mic className="w-3.5 h-3.5" /> Voice
                    </button>
                </div>

                {mode === 'text' ? (
                    <div className="space-y-3">
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            placeholder="Type to see signs..."
                            className="w-full h-32 p-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 outline-none resize-none text-sm focus:ring-2 focus:ring-[#105F68]/20 transition-all font-medium"
                        />
                        <button
                            onClick={handleTextConvert}
                            disabled={isProcessing}
                            className="w-full py-3 bg-[#105F68] text-white rounded-xl font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                        >
                            {isProcessing ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send className="w-4 h-4" />}
                            Convert to Sign
                        </button>
                    </div>
                ) : (
                    <div className="text-center space-y-4">
                        <button
                            onClick={toggleRecording}
                            className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto transition-all shadow-xl ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-[#105F68]'}`}
                        >
                            {isRecording ? <MicOff className="w-8 h-8 text-white" /> : <Mic className="w-8 h-8 text-white" />}
                        </button>
                        <div className="space-y-1">
                            <p className="text-sm font-bold text-gray-900 dark:text-gray-100">{isRecording ? "Listening..." : "Tap to speak"}</p>
                            <p className="text-[10px] text-gray-500">Speak clearly for better sign matching</p>
                        </div>
                        {transcript && (
                            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl text-xs italic text-gray-600 dark:text-gray-400">
                                "{transcript}"
                            </div>
                        )}
                    </div>
                )}

                {/* Sign Output */}
                <div className="space-y-4 pt-4">
                    <h4 className="text-xs font-black uppercase tracking-widest text-gray-400">ISL Animation</h4>
                    <div className="grid grid-cols-2 gap-3">
                        {outputSigns.length > 0 ? outputSigns.map((sign, i) => (
                            <div key={i} className="space-y-1 animate-in zoom-in duration-300" style={{ animationDelay: `${i * 0.1}s` }}>
                                <div className="aspect-video rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm transition-transform hover:scale-105">
                                    {sign.found ? (
                                        <img src={`${BACKEND_ORIGIN}${sign.gif_url}`} alt={sign.word} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-[10px] text-gray-400 text-center p-2">
                                            No sign for "{sign.word}"
                                        </div>
                                    )}
                                </div>
                                <p className="text-[10px] font-bold text-center text-[#105F68]">{sign.display_name}</p>
                            </div>
                        )) : (
                            <div className="col-span-2 py-8 text-center text-gray-400">
                                <p className="text-xs">Signs will appear here</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
