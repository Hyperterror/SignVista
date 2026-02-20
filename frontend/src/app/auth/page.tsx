"use client";

import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Mail, Lock, User, ArrowRight, Chrome, Loader2, Sparkles, Phone } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { api } from '@/app/utils/api';
import { toast } from 'sonner';
import { LoadingScreen } from '../components/LoadingScreen';

export default function AuthPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [isLogin, setIsLogin] = useState(true);
    const [phone, setPhone] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [language, setLanguage] = useState<'en' | 'hi'>('en');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [showContent, setShowContent] = useState(false);
    const circleRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    useEffect(() => {
        // High-aesthetic loading sequence
        const tl = gsap.timeline({
            onComplete: () => {
                setIsLoading(false);
                setTimeout(() => setShowContent(true), 100);
            }
        });

        tl.to(".loading-logo", { scale: 1.2, duration: 1, ease: "power2.inOut", repeat: 1, yoyo: true })
            .to(".loading-progress", { width: "100%", duration: 1.5, ease: "power1.inOut" }, "-=1");

    }, []);

    useEffect(() => {
        if (showContent) {
            gsap.fromTo(".auth-circle-container",
                { opacity: 0, scale: 0.5, rotationY: -90 },
                { opacity: 1, scale: 1, rotationY: 0, duration: 1.2, ease: "back.out(1.2)" }
            );
        }
    }, [showContent]);

    const toggleAuth = () => {
        const rotation = isLogin ? 180 : 0;
        gsap.to(circleRef.current, {
            rotateY: rotation,
            duration: 1.2,
            ease: "power3.inOut",
        });
        setIsLogin(!isLogin);
    };

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            if (isLogin) {
                const result = await api.login(phone, password);
                if (result.status === 'ok') {
                    toast.success(`Welcome back, ${result.user_name}!`);
                    setTimeout(() => router.push('/'), 1000);
                }
            } else {
                const result = await api.register({
                    name,
                    email,
                    phone,
                    password,
                    preferred_language: language
                });
                if (result.status === 'ok') {
                    toast.success(`Welcome to SignVista, ${result.user_name}!`);
                    setTimeout(() => router.push('/'), 1000);
                }
            }
        } catch (error: any) {
            toast.error(error.message || "Authentication failed");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return <LoadingScreen />;
    }

    return (
        <div className={`min-h-screen transition-colors duration-1000 flex items-center justify-center p-6 overflow-hidden perspective-[2000px] ${isLogin ? 'bg-[#0A0C10]' : 'bg-[#F8FAFB]'}`}>
            {/* Morphing background blobs */}
            <div className={`absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full blur-[120px] transition-all duration-1000 animate-pulse ${isLogin ? 'bg-[#105F68]/10' : 'bg-[#105F68]/5'}`} />
            <div className={`absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full blur-[120px] transition-all duration-1000 animate-pulse ${isLogin ? 'bg-[#08454D]/10' : 'bg-[#08454D]/5'}`} style={{ animationDelay: '1s' }} />

            <div className="auth-circle-container relative w-full max-w-[600px] aspect-square">

                {/* 3D Rotating Circle */}
                <div
                    ref={circleRef}
                    className="relative w-full h-full preserve-3d transition-transform duration-1000"
                    style={{ transformStyle: 'preserve-3d' }}
                >

                    {/* Dynamic Circle Background */}
                    <div className={`absolute inset-0 rounded-full transition-all duration-1000 shadow-2xl backdrop-blur-3xl border ${isLogin
                        ? 'bg-white/95 border-gray-100 shadow-[0_0_80px_rgba(16,95,104,0.1)]'
                        : 'bg-[#0D1117] border-white/5 shadow-[0_0_80px_rgba(16,95,104,0.3)]'
                        }`} />

                    {/* FRONT: Login Form */}
                    <div
                        className={`absolute inset-0 p-12 flex flex-col items-center justify-center backface-hidden transition-all duration-500 ${isLogin ? 'opacity-100 z-10' : 'opacity-0 z-0'}`}
                        style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                    >
                        <div className="w-full max-w-[320px] space-y-8">
                            <div className="text-center space-y-2">
                                <h2 className="text-4xl font-black text-gray-900 tracking-tight">Login</h2>
                                <p className="text-gray-500 text-sm font-medium italic">"Embark on your ISL journey"</p>
                            </div>

                            <form onSubmit={handleAuth} className="space-y-4">
                                <div className="space-y-3">
                                    <div className="relative group">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[#105F68] font-black text-xs transition-colors">+91</div>
                                        <input
                                            type="tel"
                                            required
                                            placeholder="Phone Number"
                                            className="w-full pl-14 pr-4 py-4 bg-gray-50 border border-gray-200 rounded-2xl outline-none focus:border-[#105F68]/50 focus:bg-white transition-all text-gray-900 font-medium"
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                        />
                                    </div>
                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-[#105F68] transition-colors" />
                                        <input
                                            type="password"
                                            required
                                            placeholder="Password"
                                            className="w-full pl-12 pr-4 py-4 bg-gray-50 border border-gray-200 rounded-2xl outline-none focus:border-[#105F68]/50 focus:bg-white transition-all text-gray-900 font-medium"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full py-4 bg-[#105F68] hover:bg-[#157A85] text-white rounded-2xl font-black shadow-[0_8px_20px_rgba(16,95,104,0.3)] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <>LOG IN <ArrowRight className="w-5 h-5" /></>}
                                </button>
                            </form>

                            <div className="space-y-6">
                                <div className="relative flex items-center justify-center">
                                    <div className="absolute inset-0 border-t border-gray-200 w-full" />
                                    <span className="relative bg-white px-4 text-[10px] uppercase font-black text-gray-400 tracking-[0.2em]">Social Access</span>
                                </div>

                                <button
                                    onClick={() => toast.info("Google access coming soon!")}
                                    type="button"
                                    className="w-full py-3.5 bg-gray-50 border border-gray-200 rounded-2xl flex items-center justify-center gap-3 hover:bg-gray-100 transition-all text-gray-600 font-bold text-sm"
                                >
                                    <Chrome className="w-5 h-5 text-[#4285F4]" /> Sign in with Google
                                </button>

                                <p className="text-center text-gray-500 text-sm font-bold">
                                    New here?
                                    <button onClick={toggleAuth} type="button" className="ml-2 text-[#105F68] font-black hover:underline underline-offset-4 tracking-tight">Create Account</button>
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* BACK: Signup Form */}
                    <div
                        className={`absolute inset-0 p-12 flex flex-col items-center justify-center backface-hidden transition-all duration-500 ${!isLogin ? 'opacity-100 z-10' : 'opacity-0 z-0'}`}
                        style={{ transform: 'rotateY(180deg)', backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                    >
                        <div className="w-full max-w-[340px] space-y-6">
                            <div className="text-center space-y-2">
                                <h2 className="text-3xl font-black text-white tracking-tight">Join Vista</h2>
                                <p className="text-gray-400 text-xs font-medium italic">"Create your digital ISL persona"</p>
                            </div>

                            <form onSubmit={handleAuth} className="space-y-3">
                                <div className="grid grid-cols-1 gap-3">
                                    <div className="relative group">
                                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-[#63C1BB] font-black text-xs transition-colors">+91</div>
                                        <input
                                            type="tel"
                                            required
                                            placeholder="Phone"
                                            className="w-full pl-14 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-[#63C1BB]/50 focus:bg-white/10 transition-all text-white font-medium text-sm"
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                        />
                                    </div>
                                    <div className="relative group">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-[#63C1BB] transition-colors" />
                                        <input
                                            type="email"
                                            required
                                            placeholder="Email"
                                            className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-[#63C1BB]/50 focus:bg-white/10 transition-all text-white font-medium text-sm"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                        />
                                    </div>

                                    <div className="flex gap-2">
                                        <div className="flex-1 p-1 bg-white/5 rounded-xl border border-white/10 flex">
                                            <button
                                                type="button"
                                                onClick={() => setLanguage('en')}
                                                className={`flex-1 py-2 rounded-lg text-[10px] font-black tracking-widest transition-all ${language === 'en' ? 'bg-[#63C1BB] text-white' : 'text-gray-500 hover:text-white'}`}
                                            >
                                                ENG
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setLanguage('hi')}
                                                className={`flex-1 py-2 rounded-lg text-[10px] font-black tracking-widest transition-all ${language === 'hi' ? 'bg-[#63C1BB] text-white' : 'text-gray-500 hover:text-white'}`}
                                            >
                                                HIN
                                            </button>
                                        </div>
                                    </div>

                                    <div className="relative group">
                                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-[#63C1BB] transition-colors" />
                                        <input
                                            type="password"
                                            required
                                            placeholder="Password"
                                            className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-[#63C1BB]/50 focus:bg-white/10 transition-all text-white font-medium text-sm"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                        />
                                    </div>

                                    <div className="relative group">
                                        <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-[#63C1BB] transition-colors" />
                                        <input
                                            type="text"
                                            required
                                            placeholder="Full Name"
                                            className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl outline-none focus:border-[#63C1BB]/50 focus:bg-white/10 transition-all text-white font-medium text-sm"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full py-3.5 bg-[#105F68] hover:bg-[#157A85] text-white rounded-xl font-black shadow-[0_8px_20px_rgba(16,95,104,0.3)] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
                                >
                                    {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <>START ADVENTURE <Sparkles className="w-5 h-5" /></>}
                                </button>
                            </form>

                            <p className="text-center text-gray-500 text-[11px] font-bold tracking-tight">
                                Already registered?
                                <button onClick={toggleAuth} type="button" className="ml-2 text-[#63C1BB] font-black hover:underline underline-offset-4">Sign In</button>
                            </p>
                        </div>
                    </div>

                </div>
            </div>

            <style jsx global>{`
                .backface-hidden {
                    backface-visibility: hidden;
                    -webkit-backface-visibility: hidden;
                }
                .preserve-3d {
                    transform-style: preserve-3d;
                }
                @keyframes progress {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
                .animate-progress {
                    animation: progress 2s infinite linear;
                }
            `}</style>
        </div>
    );
}
