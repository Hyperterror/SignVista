'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Type,
  Mic,
  Sparkles,
  Search,
  BookOpen,
  Users,
  Trophy,
  Moon,
  Sun,
  User as UserIcon,
  Hand
} from 'lucide-react';
import { QuickAR } from './components/QuickAR';
import { CompactStats } from './components/CompactStats';
import { api } from './utils/api';
import { useTheme } from './context/ThemeContext';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { LoadingScreen } from './components/LoadingScreen';

export default function HomePage() {
  const { theme, toggleTheme } = useTheme();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Artificial delay to show high-aesthetic loader as requested
    const sequence = async () => {
      // Step 1: Small delay for visual impact
      await new Promise(r => setTimeout(r, 2000));

      // Step 2: Check Auth
      const token = typeof window !== 'undefined' ? localStorage.getItem('signvista_access_token') : null;

      if (!token) {
        router.push('/auth');
        return;
      }

      // Step 3: Fetch Data
      try {
        const data = await api.getDashboard();
        setDashboardData(data);
        setIsLoading(false);
      } catch (error) {
        console.error('Auth verification failed:', error);
        router.push('/auth');
      }
    };

    sequence();
  }, [router]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-[#F8FAFA] dark:bg-[#0a0a0a] transition-colors duration-500 p-6 lg:p-10">
      <div className="max-w-[1600px] mx-auto space-y-10">

        {/* Header Section */}
        <header className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-4xl lg:text-5xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
                HI {dashboardData?.user_name?.toUpperCase() || 'USER'}
              </h1>
              <div className="bg-[#105F68] text-white px-3 py-1 rounded-lg text-xs font-bold animate-pulse">
                ISL GREETING ACTIVE
              </div>
            </div>
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 font-medium italic">
              <Hand className="w-5 h-5 text-[#3A9295]" />
              <span>"HI {dashboardData?.user_name || 'User'}" in sign language variant</span>
            </div>
          </div>

        </header>

        {/* Central Layout */}
        <div className="grid lg:grid-cols-4 gap-8">

          {/* Main AR Box */}
          <div className="lg:col-span-3 space-y-6">
            <div className="flex items-center justify-between px-2">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                Welcome to SignVista <Sparkles className="w-5 h-5 text-[#3A9295]" />
              </h2>
            </div>

            <div className="aspect-[16/9] lg:aspect-auto lg:h-[550px]">
              <QuickAR />
            </div>

            {/* Quick Action Buttons */}
            <div className="grid sm:grid-cols-2 gap-4">
              <Link
                href="/text"
                className="group flex items-center justify-between p-6 bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl hover:shadow-2xl transition-all border border-transparent hover:border-[#105F68]/30"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-violet-50 dark:bg-violet-950/30 flex items-center justify-center text-violet-600">
                    <Type className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="font-black text-lg text-gray-900 dark:text-gray-100">TEXT TO SIGN</h3>
                    <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Instant Conversion</p>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-gray-700 flex items-center justify-center group-hover:bg-[#105F68] group-hover:text-white transition-colors">
                  <Hand className="w-5 h-5" />
                </div>
              </Link>

              <Link
                href="/voice"
                className="group flex items-center justify-between p-6 bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl hover:shadow-2xl transition-all border border-transparent hover:border-[#3A9295]/30"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center text-blue-600">
                    <Mic className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="font-black text-lg text-gray-900 dark:text-gray-100">VOICE TO SIGN</h3>
                    <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Real-time Recognition</p>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-full bg-gray-50 dark:bg-gray-700 flex items-center justify-center group-hover:bg-[#3A9295] group-hover:text-white transition-colors">
                  <Mic className="w-5 h-5" />
                </div>
              </Link>
            </div>
          </div>

          {/* Features Side Column */}
          <div className="space-y-6">
            <div className="bg-[#105F68] rounded-[2.5rem] p-8 text-white shadow-2xl relative overflow-hidden group">
              <div className="absolute -right-8 -bottom-8 opacity-10 group-hover:scale-110 transition-transform duration-700">
                <Sparkles className="w-48 h-48" />
              </div>
              <h3 className="text-2xl font-black mb-4 relative z-10 leading-tight">EXPLORE OUR FEATURES</h3>
              <p className="text-sm opacity-80 mb-8 relative z-10 leading-relaxed font-medium">
                Bridge the communication gap with ISL. Learn, search, and connect with the deaf community through our specialized tools.
              </p>

              <div className="space-y-4 relative z-10">
                <Link href="/dictionary" className="flex items-center gap-3 p-3 bg-white/10 rounded-2xl hover:bg-white/20 transition-colors border border-white/10">
                  <Search className="w-5 h-5" />
                  <span className="font-bold text-sm">ISL Dictionary</span>
                </Link>
                <Link href="/learning" className="flex items-center gap-3 p-3 bg-white/10 rounded-2xl hover:bg-white/20 transition-colors border border-white/10">
                  <BookOpen className="w-5 h-5" />
                  <span className="font-bold text-sm">Learning Path</span>
                </Link>
                <Link href="/game" className="flex items-center gap-3 p-3 bg-white/10 rounded-2xl hover:bg-white/20 transition-colors border border-white/10">
                  <Trophy className="w-5 h-5" />
                  <span className="font-bold text-sm">Sign Quiz Rush</span>
                </Link>
                <Link href="/community" className="flex items-center gap-3 p-3 bg-white/10 rounded-2xl hover:bg-white/20 transition-colors border border-white/10">
                  <Users className="w-5 h-5" />
                  <span className="font-bold text-sm">ISL Community</span>
                </Link>
              </div>
            </div>

            {/* Daily Tip */}
            <div className="bg-white dark:bg-gray-800 rounded-[2.5rem] p-8 border border-gray-100 dark:border-gray-700 shadow-xl">
              <h4 className="text-[#105F68] font-black tracking-widest text-[10px] mb-4 uppercase">Daily Sign Tip</h4>
              <p className="text-gray-600 dark:text-gray-400 text-sm font-medium leading-relaxed">
                "When signing names, ensure your dominant hand is clear and your movements are crisp."
              </p>
            </div>
          </div>
        </div>

        {/* Analytics Footer Section */}
        <footer className="pt-6 border-t border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 uppercase tracking-tighter">Your Progress Insights</h2>
            <Link href="/dashboard" className="text-sm font-bold text-[#105F68] hover:underline flex items-center gap-1">
              Full Analytics <Sparkles className="w-4 h-4" />
            </Link>
          </div>
          {dashboardData && <CompactStats data={dashboardData} />}
        </footer>

      </div>
    </div>
  );
}
