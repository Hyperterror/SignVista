'use client';

import { useState, useEffect } from 'react';
import { User, Mail, Phone, Globe, Save } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'sonner';

export default function ProfilePage() {
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    const [formData, setFormData] = useState({
        name: '',
        email: '',
        phone: '',
        preferred_language: 'en'
    });

    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        setIsLoading(true);
        try {
            const res = await api.getMe();
            setFormData({
                name: res.name || '',
                email: res.email || '',
                phone: res.phone || '',
                preferred_language: res.preferred_language || 'en'
            });
        } catch (e) {
            toast.error("Failed to load profile");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);
        try {
            await api.updateProfile(formData.name, formData.email, formData.phone);
            toast.success("Profile updated successfully!");
        } catch (e: any) {
            toast.error(e.message || "Failed to update profile");
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-[#105F68] border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen p-6 md:p-12">
            <div className="max-w-3xl mx-auto">
                <div className="mb-10">
                    <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[#105F68] to-[#3A9295] bg-clip-text text-transparent">
                        Your Profile
                    </h1>
                    <p className="text-lg text-gray-500 mt-2">Manage your account details and learning preferences.</p>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-[40px] shadow-2xl border border-gray-100 dark:border-gray-800 p-8 md:p-12">
                    <div className="flex items-center gap-6 mb-12">
                        <div className="w-24 h-24 bg-gradient-to-tr from-[#105F68] to-[#3A9295] rounded-3xl flex items-center justify-center shadow-lg text-4xl text-white font-black">
                            {formData.name.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold">{formData.name}</h2>
                            <p className="text-gray-500">SignVista Learner</p>
                        </div>
                    </div>

                    <form onSubmit={handleSave} className="space-y-6">
                        <div className="grid md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <User className="w-4 h-4 text-[#105F68]" /> Full Name
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full h-14 bg-gray-50 dark:bg-gray-800 border-none rounded-2xl px-4 font-medium focus:ring-2 focus:ring-[#105F68]"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <Mail className="w-4 h-4 text-[#105F68]" /> Email Address
                                </label>
                                <input
                                    type="email"
                                    required
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full h-14 bg-gray-50 dark:bg-gray-800 border-none rounded-2xl px-4 font-medium focus:ring-2 focus:ring-[#105F68]"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <Phone className="w-4 h-4 text-[#105F68]" /> Phone Number
                                </label>
                                <input
                                    type="tel"
                                    disabled
                                    value={formData.phone}
                                    className="w-full h-14 bg-gray-100 dark:bg-gray-900 border-none rounded-2xl px-4 font-medium text-gray-400 cursor-not-allowed"
                                />
                                <p className="text-xs text-gray-500">Phone number cannot be changed.</p>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                                    <Globe className="w-4 h-4 text-[#105F68]" /> Preferred Language
                                </label>
                                <select
                                    value={formData.preferred_language}
                                    onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
                                    className="w-full h-14 bg-gray-50 dark:bg-gray-800 border-none rounded-2xl px-4 font-medium focus:ring-2 focus:ring-[#105F68]"
                                >
                                    <option value="en">English</option>
                                    <option value="hi">Hindi</option>
                                </select>
                            </div>
                        </div>

                        <div className="pt-8 mt-8 border-t border-gray-100 dark:border-gray-800 flex justify-end">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="px-8 py-4 bg-gradient-to-r from-[#105F68] to-[#3A9295] text-white rounded-2xl font-bold flex items-center gap-3 hover:shadow-lg hover:-translate-y-0.5 transition-all disabled:opacity-50"
                            >
                                {isSaving ? (
                                    <span className="animate-spin text-xl">↻</span>
                                ) : (
                                    <><Save className="w-5 h-5" /> Save Profile</>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
