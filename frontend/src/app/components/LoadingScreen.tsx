"use client";

import React from 'react';
import { Sparkles } from 'lucide-react';

export const LoadingScreen = () => {
  return (
    <div className="min-h-screen bg-[#0A0C10] flex flex-col items-center justify-center p-6 z-[9999] fixed inset-0">
      {/* Morphing background blobs */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#105F68]/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#08454D]/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />

      <div className="loading-logo relative mb-8">
        <div className="w-24 h-24 bg-[#105F68]/20 rounded-full flex items-center justify-center border border-[#105F68]/30">
          <Sparkles className="w-12 h-12 text-[#105F68]" />
        </div>
        <div className="absolute inset-[-8px] border-2 border-[#105F68]/10 rounded-full animate-ping" />
      </div>
      <h1 className="text-3xl font-black text-white tracking-[0.3em] mb-4">SIGNVISTA</h1>
      <div className="w-64 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
        <div className="loading-progress h-full bg-gradient-to-r from-[#105F68] to-[#2DA4A8] w-0 animate-progress-glow" />
      </div>
      <p className="mt-4 text-[#105F68] font-bold text-xs tracking-widest uppercase animate-pulse">Initializing Core...</p>

      <style jsx>{`
                .animate-progress-glow {
                    animation: grow 2s ease-in-out infinite;
                }
                @keyframes grow {
                    0% { width: 0%; opacity: 0.5; }
                    50% { width: 70%; opacity: 1; }
                    100% { width: 100%; opacity: 0.5; }
                }
            `}</style>
    </div>
  );
};
