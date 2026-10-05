'use client';

import { useState, useEffect } from 'react';
import { Settings, Moon, Sun, Volume2, Bell, X, Save } from 'lucide-react';
import { ThemePreference, useTheme } from '../context/ThemeContext';
import { api } from '../utils/api';
import { toast } from 'sonner';

interface SettingsDialogProps {
    isOpen: boolean;
    onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
    const { preference, setPreference } = useTheme();
    const [isLoading, setIsLoading] = useState(false);
    const [settings, setSettings] = useState({
        theme: preference as string,
        notifications_enabled: true,
        sound_enabled: true,
        daily_goal_minutes: 15
    });

    useEffect(() => {
        if (isOpen) {
            loadSettings();
        }
    }, [isOpen]);

    const loadSettings = async () => {
        try {
            const res = await api.getSettings();
            setSettings({
                theme: res.theme,
                notifications_enabled: res.notifications_enabled,
                sound_enabled: res.sound_enabled,
                daily_goal_minutes: res.daily_goal_minutes
            });
        } catch (e: any) {
            toast.error(e.message || 'Could not load settings');
        }
    };

    const handleSave = async () => {
        setIsLoading(true);
        try {
            await api.updateSettings(settings);
            setPreference(settings.theme as ThemePreference);
            window.dispatchEvent(new CustomEvent('signvista:settings', { detail: settings }));
            toast.success('Settings updated!');
            onClose();
        } catch (e: any) {
            toast.error(e.message || 'Failed to update settings');
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
            <div className="bg-white dark:bg-gray-900 w-full max-w-md rounded-3xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">

                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-xl">
                            <Settings className="w-6 h-6 text-[#105F68]" />
                        </div>
                        <h2 className="text-xl font-bold">Preferences</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors">
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Form Body */}
                <div className="p-6 space-y-6">

                    {/* Theme */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {settings.theme === 'dark' ? <Moon className="w-5 h-5 text-gray-500" /> : <Sun className="w-5 h-5 text-gray-500" />}
                            <div>
                                <p className="font-semibold text-gray-900 dark:text-gray-100">Display Theme</p>
                                <p className="text-xs text-gray-500">Choose your visual preference</p>
                            </div>
                        </div>
                        <select
                            value={settings.theme}
                            onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                            className="bg-gray-50 dark:bg-gray-800 border-none rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#105F68]"
                        >
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="system">System</option>
                        </select>
                    </div>

                    {/* Sound */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Volume2 className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="font-semibold text-gray-900 dark:text-gray-100">Voice Feedback</p>
                                <p className="text-xs text-gray-500">Speak recognized signs aloud while translating</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                className="sr-only peer"
                                checked={settings.sound_enabled}
                                onChange={(e) => setSettings({ ...settings, sound_enabled: e.target.checked })}
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#105F68]"></div>
                        </label>
                    </div>

                    {/* Notifications */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Bell className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="font-semibold text-gray-900 dark:text-gray-100">Notifications</p>
                                <p className="text-xs text-gray-500">Show the unread badge for level-ups and achievements</p>
                            </div>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                className="sr-only peer"
                                checked={settings.notifications_enabled}
                                onChange={(e) => setSettings({ ...settings, notifications_enabled: e.target.checked })}
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-[#105F68]"></div>
                        </label>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 dark:bg-gray-800/30 border-t border-gray-100 dark:border-gray-800">
                    <button
                        onClick={handleSave}
                        disabled={isLoading}
                        className="w-full py-3 bg-gradient-to-r from-[#105F68] to-[#3A9295] text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:shadow-lg transition-all disabled:opacity-50"
                    >
                        {isLoading ? <span className="animate-spin text-xl">↻</span> : <><Save className="w-5 h-5" /> Save Changes</>}
                    </button>
                </div>
            </div>
        </div>
    );
}
