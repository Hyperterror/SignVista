'use client';

import { FloatingParticles } from '../components/learn/FloatingParticles';
import { RightProfilePanel } from '../components/learn/RightProfilePanel';
import { RotatingQuote } from '../components/learn/RotatingQuote';
import { NavigationPillBar } from '../components/learn/NavigationPillBar';
import { ISLDictionaryPanel } from '../components/learn/ISLDictionaryPanel';
import { useState } from 'react';

export default function LearnDashboard() {
    const [activeTab, setActiveTab] = useState<'dictionary' | 'practice' | 'matrix'>('dictionary');

    return (
        <div className="min-h-screen pl-[70px] lg:pl-[260px] transition-all duration-300 relative overflow-hidden bg-gradient-to-br from-[#344C3D] via-[#105F68] to-[#3A9295]">
            {/* Background Particles */}
            <FloatingParticles />

            <div className="relative z-10 flex h-screen max-w-7xl mx-auto">
                {/* Main Content Area */}
                <div className="flex-1 flex flex-col pt-12 px-8 overflow-y-auto scrollbar-hide">

                    {/* Top Rotating Quote */}
                    <div className="mb-8">
                        <RotatingQuote />
                    </div>

                    {/* Navigation Tab Pill */}
                    <div className="mb-10 w-full flex justify-center">
                        <NavigationPillBar activeTab={activeTab} setActiveTab={setActiveTab} />
                    </div>

                    {/* Tab Content Panel */}
                    <div className="flex-1 pb-12 w-full max-w-5xl mx-auto">
                        {activeTab === 'dictionary' && (
                            <ISLDictionaryPanel />
                        )}
                        {activeTab === 'practice' && (
                            <div className="text-white text-center animate-pulse">Practice Lessons module coming soon...</div>
                        )}
                        {activeTab === 'matrix' && (
                            <div className="text-white text-center animate-pulse">Proficiency Matrix module coming soon...</div>
                        )}
                    </div>
                </div>

                {/* Right Sidebar Panel */}
                <RightProfilePanel />
            </div>
        </div>
    );
}
