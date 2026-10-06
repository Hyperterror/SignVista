"use client";
import Image from 'next/image';

import React from 'react';

export const LoadingScreen = () => {
  return (
    <div className="min-h-screen bg-[#F8F9FF] flex flex-col items-center justify-center p-6 z-[9999] fixed inset-0 overflow-hidden select-none">

      {/* 3D Hand Container */}
      <div className="relative w-full max-w-[95vw] md:max-w-[70vw] aspect-[16/9] flex items-center justify-center mt-[-5%]">

        {/* Bobbing Motion Wrapper for the true 3D image */}
        <div className="relative w-full h-full flex items-center justify-center animate-bob">

          {/* Authentic 3D Hand Image */}
          <div className="relative z-20 w-full h-full flex flex-col items-center justify-center">
            <Image
              src="/assets/images/yellow-hand-nobg.png"
              alt="3D Waving Hand"
              fill
              priority
              sizes="(min-width: 768px) 70vw, 95vw"
              className="object-contain filter drop-shadow-[0_40px_60px_rgba(0,0,0,0.15)] select-none scale-125 md:scale-150 animate-wave"
              draggable={false}
            />
          </div>

          {/* Deep Shadow for realism (syncs with bobbing) */}
          <div className="absolute bottom-[-10%] w-[50%] h-[15%] bg-black/10 rounded-[100%] blur-3xl scale-y-[0.3] animate-shadow-sync z-10" />
        </div>
      </div>

      <div className="mt-4 text-center relative z-30">
        <h1 className="text-xl font-bold text-[#1A1A1A]/50 tracking-[0.8em] uppercase ml-[0.8em] mb-4 drop-shadow-sm">SIGNVISTA</h1>
        <div className="relative w-48 h-1.5 bg-black/[0.03] rounded-full overflow-hidden mx-auto shadow-inner">
          <div className="absolute inset-0 bg-gradient-to-r from-[#FFD600] to-[#FFAB00] w-1/3 animate-dash rounded-full shadow-[0_0_12px_rgba(255,214,0,0.6)]" />
        </div>
      </div>
    </div>
  );
};
