'use client';

import { Bell, Moon, Sun, User } from 'lucide-react';
import Link from 'next/link';
import { useTheme } from '../context/ThemeContext';
import { toast } from 'sonner';

export function HeaderActions() {
    const { theme, toggleTheme } = useTheme();

    const handleNotifications = () => {
        toast.info('No new notifications', {
            description: 'You are all caught up!',
        });
    };

    return (
        <div className="fixed top-4 right-4 lg:top-6 lg:right-6 z-50 flex items-center gap-2 lg:gap-3">
            {/* Notifications */}
            <button
                onClick={handleNotifications}
                className="w-10 h-10 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 flex items-center justify-center hover:scale-110 transition-all hover:bg-gray-50 dark:hover:bg-gray-700 group"
            >
                <Bell className="w-4 h-4 lg:w-5 lg:h-5 text-gray-400 group-hover:text-[#105F68] dark:group-hover:text-[#63C1BB]" />
            </button>

            {/* Theme Toggle */}
            <button
                onClick={toggleTheme}
                className="w-10 h-10 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-white dark:bg-gray-800 shadow-xl border border-gray-100 dark:border-gray-700 flex items-center justify-center hover:scale-110 transition-all hover:bg-gray-50 dark:hover:bg-gray-700 group"
            >
                {theme === 'dark' ? (
                    <Sun className="w-4 h-4 lg:w-5 lg:h-5 text-yellow-500" />
                ) : (
                    <Moon className="w-4 h-4 lg:w-5 lg:h-5 text-gray-400 group-hover:text-indigo-600" />
                )}
            </button>

            {/* Profile Link */}
            <Link
                href="/profile"
                className="w-10 h-10 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-gradient-to-br from-[#105F68] to-[#3A9295] shadow-xl flex items-center justify-center hover:scale-110 transition-all border-2 border-white dark:border-gray-800"
            >
                <User className="w-4 h-4 lg:w-5 lg:h-5 text-white" />
            </Link>
        </div>
    );
}
