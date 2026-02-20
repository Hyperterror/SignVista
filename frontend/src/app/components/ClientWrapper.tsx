'use client';

import { useState, useEffect } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { Sidebar } from './Sidebar';
import { LoadingScreen } from './LoadingScreen';
import { Toaster } from './Toaster';

export function ClientWrapper({ children }: { children: React.ReactNode }) {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Show loading screen on first load
        const timer = setTimeout(() => setLoading(false), 2500);
        return () => clearTimeout(timer);
    }, []);

    if (loading) {
        return <LoadingScreen />;
    }

    return (
        <ThemeProvider>
            <div className="flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
                <Toaster />
                <Sidebar />
                <main className="flex-1 ml-0 lg:ml-[20%] overflow-x-hidden">
                    {children}
                </main>
            </div>
        </ThemeProvider>
    );
}
