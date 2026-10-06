"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Camera, CameraOff, Activity, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { api } from "../../utils/api";
import { SignMedia } from "../SignMedia";
import { AG_EASE, DictionaryWord, ProgressWord, VocabularyWord, prettyWord } from "../../learning/types";

const FRAME_INTERVAL_MS = 150;

interface Feedback {
    message: string;
    correct: boolean | null;
    predicted: string | null;
    proficiency: number;
    attempts: number;
}

export function PracticePanel({
    vocabulary,
    progress,
    dictionary,
    initialWord,
    onAttempt,
}: {
    vocabulary: VocabularyWord[];
    progress: ProgressWord[];
    dictionary: DictionaryWord[];
    initialWord?: string | null;
    onAttempt: () => void;
}) {
    const practicable = vocabulary.filter((v) => v.recognizable);
    const findPracticable = (w?: string | null) =>
        w ? practicable.find((v) => v.word.toLowerCase() === w.toLowerCase())?.word ?? null : null;

    const [target, setTarget] = useState<string | null>(findPracticable(initialWord) ?? practicable[0]?.word ?? null);
    const [isActive, setIsActive] = useState(false);
    const [feedback, setFeedback] = useState<Feedback | null>(null);

    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const loopRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const activeRef = useRef(false);
    const targetRef = useRef(target);

    useEffect(() => { targetRef.current = target; }, [target]);

    // The parent remounts this panel (key) when a new word is requested
    useEffect(() => {
        if (initialWord && !findPracticable(initialWord)) {
            toast.info(`"${prettyWord(initialWord)}" can't be practiced with the camera yet.`);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const stop = () => {
        activeRef.current = false;
        if (loopRef.current) clearTimeout(loopRef.current);
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setIsActive(false);
    };

    useEffect(() => stop, []);

    const loop = async () => {
        if (!activeRef.current) return;
        const video = videoRef.current;
        const word = targetRef.current;
        if (video && word && video.readyState >= 2 && video.videoWidth) {
            const canvas = canvasRef.current ?? (canvasRef.current = document.createElement("canvas"));
            canvas.width = 480;
            canvas.height = Math.round(480 * video.videoHeight / video.videoWidth);
            const ctx = canvas.getContext("2d");
            if (ctx) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                try {
                    const res = await api.learnAttempt(word, canvas.toDataURL("image/jpeg", 0.6));
                    const recorded = res.predicted !== null;
                    if (recorded) onAttempt();
                    setFeedback((prev) => ({
                        message: res.fault || prev?.message || "",
                        correct: recorded ? res.correct : prev?.correct ?? null,
                        predicted: recorded ? res.predicted : prev?.predicted ?? null,
                        proficiency: res.proficiency,
                        attempts: res.attempts,
                    }));
                    if (recorded && res.correct) toast.success(`Correct: ${prettyWord(word)}! +10 XP`);
                } catch (e: any) {
                    toast.error(e.message || "Practice failed");
                    stop();
                    return;
                }
            }
        }
        if (activeRef.current) loopRef.current = setTimeout(loop, FRAME_INTERVAL_MS);
    };

    const start = async () => {
        if (!target) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: "user" } });
            streamRef.current = stream;
            if (videoRef.current) videoRef.current.srcObject = stream;
            activeRef.current = true;
            setIsActive(true);
            setFeedback(null);
            loopRef.current = setTimeout(loop, 300);
        } catch {
            toast.error("Camera access is required to practice.");
        }
    };

    const demo = dictionary.find((d) => d.word === target?.toLowerCase());
    const needsWork = progress.filter((w) => w.attempts > 0 && w.proficiency < 60).sort((a, b) => a.proficiency - b.proficiency).slice(0, 4);

    if (practicable.length === 0) {
        return (
            <p className="text-center text-gray-500 py-12">
                Camera practice is unavailable because no sign recognition model is loaded.
            </p>
        );
    }

    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-5xl flex flex-col gap-8">
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: AG_EASE }}
                    className="w-full bg-white dark:bg-gray-800 rounded-[24px] border border-gray-100 dark:border-gray-700 p-6 md:p-8 shadow-xl"
                >
                    <div className="flex flex-wrap items-center gap-3 mb-6">
                        <Sparkles className="w-5 h-5 text-[#105F68] dark:text-[#9ED5D1]" />
                        <span className="text-sm font-bold text-[#105F68] dark:text-[#63C1BB] uppercase tracking-wider">Choose a sign</span>
                        <select
                            value={target ?? ""}
                            onChange={(e) => { setTarget(e.target.value); setFeedback(null); }}
                            className="ml-auto px-4 py-2 rounded-xl bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 font-bold"
                        >
                            {practicable.map((v) => (
                                <option key={v.word} value={v.word}>{v.display_name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                        <div>
                            <SignMedia gifUrl={demo?.gif_url} label={target ? prettyWord(target) : ""} className="w-full aspect-video rounded-2xl" />
                            <p className="text-sm text-gray-600 dark:text-gray-300 mt-4">
                                {demo?.description ?? `Perform the sign for "${target ? prettyWord(target) : ""}" clearly in front of the camera.`}
                            </p>
                        </div>
                        <div className="flex flex-col gap-4">
                            <div className="relative aspect-video bg-black rounded-2xl overflow-hidden">
                                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />
                                {!isActive && (
                                    <div className="absolute inset-0 flex items-center justify-center text-white/60 text-sm">Camera off</div>
                                )}
                            </div>
                            <button
                                onClick={isActive ? stop : start}
                                className={`py-3 rounded-xl font-bold flex items-center justify-center gap-2 ${isActive ? 'bg-red-500 text-white' : 'bg-[#105F68] text-white'}`}
                            >
                                {isActive ? <><CameraOff className="w-5 h-5" /> Stop</> : <><Camera className="w-5 h-5" /> Start practicing</>}
                            </button>
                            {feedback && (
                                <div className={`p-4 rounded-2xl text-sm font-medium ${feedback.correct === true ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300' : feedback.correct === false ? 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-300' : 'bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-300'}`}>
                                    <p>{feedback.message}</p>
                                    {feedback.predicted && feedback.correct === false && (
                                        <p className="mt-1 text-xs">Detected: {prettyWord(feedback.predicted)}</p>
                                    )}
                                    <p className="mt-2 text-xs opacity-80">
                                        Proficiency {Math.round(feedback.proficiency)}% over {feedback.attempts} attempt{feedback.attempts === 1 ? '' : 's'}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>

                {needsWork.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {needsWork.map((w, idx) => (
                            <motion.div
                                key={w.word}
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.8, delay: 0.2 + idx * 0.1, ease: AG_EASE }}
                                className="bg-white dark:bg-gray-800/80 rounded-2xl border border-gray-100 dark:border-gray-700 p-6 flex flex-col"
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{w.display_name}</h3>
                                    <span className="flex items-center gap-2 text-sm text-gray-500">
                                        <Activity className="w-4 h-4" /> {Math.round(w.proficiency)}%
                                    </span>
                                </div>
                                <div className="w-full bg-gray-100 dark:bg-gray-900 h-3 rounded-full overflow-hidden mb-4">
                                    <div className="h-full bg-gradient-to-r from-[#105F68] to-[#3A9295]" style={{ width: `${w.proficiency}%` }} />
                                </div>
                                <button
                                    onClick={() => { setTarget(findPracticable(w.word) ?? target); setFeedback(null); }}
                                    className="mt-auto text-sm font-bold text-[#105F68] dark:text-[#9ED5D1] hover:underline self-start"
                                >
                                    Practice again →
                                </button>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
