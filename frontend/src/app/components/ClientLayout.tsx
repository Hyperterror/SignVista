'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { HeaderActions } from './HeaderActions';
import { Toaster } from './Toaster';
import { ThemeProvider } from '../context/ThemeContext';
import { useSidebar } from '../context/SidebarContext';

import { useState, useEffect } from 'react';
import { LoadingScreen } from './LoadingScreen';

export function ClientLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isPublicRoute = pathname === '/auth' || pathname === '/';
    const { isExpanded } = useSidebar();
    const [isLoading, setIsLoading] = useState(true);
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        // Show loading screen for 1 second, then fade out
        const timer1 = setTimeout(() => {
            setIsFading(true);
        }, 1000);

        // Unmount loading screen after fade completes
        const timer2 = setTimeout(() => {
            setIsLoading(false);
        }, 1300); // 1000ms + 300ms transition

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
        };
    }, []);

    return (
        <ThemeProvider>
            {isLoading && (
                <div className={`fixed inset-0 z-[9999] transition-opacity duration-300 ${isFading ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                    <LoadingScreen />
                </div>
            )}
            <div className={`flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-opacity duration-300 ${isLoading && !isFading ? 'opacity-0' : 'opacity-100'}`}>
                <Toaster />
                {!isPublicRoute && <HeaderActions />}
                {!isPublicRoute && <Sidebar />}
                <main
                    className={`flex-1 transition-all duration-[300ms] ease-[cubic-bezier(0.25,1,0.5,1)] overflow-x-hidden ${!isPublicRoute ? '' : 'ml-0'}`}
                    style={{
                        marginLeft: !isPublicRoute ? (isExpanded ? '280px' : '88px') : '0',
                    }}
                >
                    {children}
                </main>
            </div>
        </ThemeProvider>
    );
}
