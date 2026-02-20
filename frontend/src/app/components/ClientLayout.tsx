"use client";

import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { HeaderActions } from './HeaderActions';
import { Toaster } from './Toaster';
import { ThemeProvider } from '../context/ThemeContext';

export function ClientLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isAuthPage = pathname === '/auth';

    return (
        <ThemeProvider>
            <div className="flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
                <Toaster />
                {!isAuthPage && <HeaderActions />}
                {!isAuthPage && <Sidebar />}
                <main className={`flex-1 transition-all duration-300 overflow-x-hidden ${!isAuthPage ? 'ml-0 lg:ml-20' : 'ml-0'}`}>
                    {children}
                </main>
            </div>
        </ThemeProvider>
    );
}
