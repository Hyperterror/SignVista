'use client';

import React from 'react';
import { useSidebar } from '../context/SidebarContext';
import { Sidebar } from './Sidebar';

export function ClientLayout({ children }: { children: React.ReactNode }) {
    const { isExpanded } = useSidebar();

    return (
        <div className="flex min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
            <Sidebar />
            <main
                className={`flex-1 transition-all duration-[300ms] ease-[cubic-bezier(0.25,1,0.5,1)] overflow-x-hidden`}
                style={{
                    marginLeft: isExpanded ? '260px' : '70px',
                }}
            >
                {children}
            </main>
        </div>
    );
}
