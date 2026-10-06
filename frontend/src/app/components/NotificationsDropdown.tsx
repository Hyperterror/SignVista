'use client';

import { useState, useEffect } from 'react';
import { Bell, Check, CheckCircle2, AlertCircle, Info, Trophy } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { api } from '../utils/api';
import { formatRelative, useNow } from '../utils/time';
import { motion } from 'framer-motion';

interface NotificationsDropdownProps {
    isOpen: boolean;
    onClose: () => void;
    onUnreadChange?: (count: number) => void;
}

export function NotificationsDropdown({ isOpen, onClose, onUnreadChange }: NotificationsDropdownProps) {
    const router = useRouter();
    const now = useNow();
    const [notifications, setNotifications] = useState<any[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);


    const markAllRead = async () => {
        try {
            await api.markAllNotificationsRead();
            setNotifications(notifications.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
            onUnreadChange?.(0);
        } catch (e) {
            console.error(e);
        }
    };

    const markRead = async (id: number) => {
        try {
            await api.markNotificationRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
            setUnreadCount(prev => {
                const next = Math.max(0, prev - 1);
                onUnreadChange?.(next);
                return next;
            });
        } catch {
            // non-critical; the badge refreshes on next open
        }
    };

    useEffect(() => {
        if (!isOpen) return;
        let ignore = false;
        api.getNotifications()
            .then((res) => {
                if (ignore) return;
                setNotifications(res.notifications);
                setUnreadCount(res.unread_count);
                onUnreadChange?.(res.unread_count);
            })
            .catch((e) => console.error('Failed to load notifications', e));
        return () => { ignore = true; };
    }, [isOpen, onUnreadChange]);

    if (!isOpen) return null;


    const getIcon = (type: string) => {
        switch (type) {
            case 'success': return <CheckCircle2 className="w-5 h-5 text-green-500" />;
            case 'achievement': return <Trophy className="w-5 h-5 text-yellow-500" />;
            case 'warning': return <AlertCircle className="w-5 h-5 text-orange-500" />;
            default: return <Info className="w-5 h-5 text-blue-500" />;
        }
    };

    return (
        <>
            <div className="fixed inset-0 z-40" onClick={onClose} />
            <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed bottom-24 left-24 w-80 bg-white dark:bg-gray-900 rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden z-50 flex flex-col max-h-[400px]"
            >
                <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-800/30">
                    <div className="flex items-center gap-2">
                        <h3 className="font-bold">Notifications</h3>
                        {unreadCount > 0 && (
                            <span className="bg-[#105F68] text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                                {unreadCount} New
                            </span>
                        )}
                    </div>
                    {unreadCount > 0 && (
                        <button onClick={markAllRead} className="text-xs font-semibold text-gray-500 hover:text-[#105F68] flex items-center gap-1">
                            <Check className="w-3 h-3" /> Mark all read
                        </button>
                    )}
                </div>

                <div className="overflow-y-auto flex-1 p-2 space-y-1 custom-scrollbar">
                    {notifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                            <Bell className="w-12 h-12 mb-3 opacity-20" />
                            <p className="text-sm">You&apos;re all caught up!</p>
                        </div>
                    ) : (
                        notifications.map((n) => (
                            <div
                                key={n.id}
                                onClick={() => {
                                    if (!n.is_read) markRead(n.id);
                                    if (n.action_url && n.action_url.startsWith('/')) {
                                        onClose();
                                        router.push(n.action_url);
                                    }
                                }}
                                className={`
                            p-3 rounded-2xl flex gap-3 transition-colors cursor-pointer
                            ${n.is_read ? 'opacity-60 hover:bg-gray-50 dark:hover:bg-gray-800' : 'bg-blue-50/50 dark:bg-[#105F68]/10 hover:bg-blue-50 dark:hover:bg-[#105F68]/20'}
                        `}
                            >
                                <div className="shrink-0 mt-0.5">
                                    {getIcon(n.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className={`text-sm ${n.is_read ? 'text-gray-700 dark:text-gray-300' : 'font-bold text-gray-900 dark:text-white'}`}>
                                        {n.title}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1 leading-snug">{n.message}</p>
                                    <p className="text-[10px] text-gray-400 mt-2 font-medium">{formatRelative(n.timestamp, now)}</p>
                                </div>
                                {!n.is_read && (
                                    <div className="shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-1.5" />
                                )}
                            </div>
                        ))
                    )}
                </div>
            </motion.div>
        </>
    );
}
