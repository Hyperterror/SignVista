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
    const isAuthPage = pathname === '/auth';
    const { isExpanded } = useSidebar();
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Show loading screen for 2.5 seconds
        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 2500);
        return () => clearTimeout(timer);
    }, []);

    return (
        <ThemeProvider>
            {isLoading && <LoadingScreen />}
            <div className={`flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
                <Toaster />
                {!isAuthPage && <HeaderActions />}
                {!isAuthPage && <Sidebar />}
                <main
                    className={`flex-1 transition-all duration-[300ms] ease-[cubic-bezier(0.25,1,0.5,1)] overflow-x-hidden ${!isAuthPage ? '' : 'ml-0'}`}
                    style={{
                        marginLeft: !isAuthPage ? (isExpanded ? '280px' : '88px') : '0',
                    }}
                >
                    {children}
                </main>
            </div>
        </ThemeProvider>
    );
}
