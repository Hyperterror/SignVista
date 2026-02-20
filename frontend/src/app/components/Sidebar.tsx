'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import {
  Home,
  LayoutDashboard,
  BookOpen,
  Search,
  Users,
  Camera,
  Type,
  Mic,
  Star,
  User,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Award,
  Trophy,
  Activity,
  Menu,
  X,
  Sun,
  Moon,
  Hand
} from 'lucide-react';

export function Sidebar() {
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const navItems = [
    { path: '/', icon: Home, label: 'Home', gesture: '🏠' },
    { path: '/profile', icon: User, label: 'Profile', gesture: '👤' },
    { path: '/game', icon: Trophy, label: 'ISL Quiz Game', gesture: '🎮' },
    { path: '/learning', icon: BookOpen, label: 'Learning Hub', gesture: '📚' },
    { path: '/dictionary', icon: Search, label: 'ISL Dictionary', gesture: '🔎' },
    { path: '/community', icon: Users, label: 'Community', gesture: '🤝' },
    { path: '/translate', icon: Camera, label: 'AR Translate', gesture: '📸' },
    { path: '/text', icon: Type, label: 'Text to Sign', gesture: '✍️' },
    { path: '/voice', icon: Mic, label: 'Voice to Sign', gesture: '🎤' },
  ];

  const handleMobileToggle = () => {
    setIsMobileOpen(!isMobileOpen);
    if (!isMobileOpen) {
      gsap.fromTo('.mobile-nav-item',
        { x: -20, opacity: 0 },
        { x: 0, opacity: 1, stagger: 0.1, duration: 0.4, ease: 'power2.out' }
      );
    }
  };

  return (
    <>
      {/* Mobile Toggle */}
      <button
        onClick={handleMobileToggle}
        className="lg:hidden fixed top-4 left-4 z-50 p-3 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700 hover:scale-105 transition-transform"
      >
        {isMobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Sidebar Desktop */}
      <motion.aside
        initial={false}
        animate={{
          width: isHovered ? 280 : 88,
          x: isMobileOpen ? 0 : (typeof window !== 'undefined' && window.innerWidth < 1024 ? -280 : 0)
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`
          fixed left-0 top-0 h-full bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800 
          z-40 overflow-hidden shadow-2xl transition-colors duration-500
        `}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        <div className="flex flex-col h-full py-6 px-4">
          {/* Logo Area */}
          <div className="mb-10 flex items-center gap-4 px-2 overflow-hidden">
            <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-[#105F68] to-[#3A9295] rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-300">
              <Hand className="w-7 h-7 text-white" />
            </div>
            <motion.div
              animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : -20 }}
              className="flex-shrink-0"
            >
              <h1 className="text-2xl font-black text-[#105F68] dark:text-[#63C1BB] tracking-tight whitespace-nowrap">SignBridge</h1>
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500 whitespace-nowrap">Real-Time Translation</span>
            </motion.div>
          </div>

          {/* Nav Section */}
          <nav className="flex-1 space-y-2">
            {navItems.map((item) => {
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  onClick={() => setIsMobileOpen(false)}
                  className={`
                    group flex items-center gap-4 px-3.5 py-3.5 rounded-2xl transition-all duration-300 relative overflow-hidden
                    ${isActive
                      ? 'bg-gradient-to-r from-[#105F68] to-[#3A9295] text-white shadow-lg'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-[#105F68] dark:hover:text-[#63C1BB]'}
                  `}
                >
                  <item.icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-300 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
                  <motion.span
                    animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : -10 }}
                    className="font-semibold text-sm whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                  {isActive && isHovered && (
                    <div className="absolute right-0 top-0 h-full w-1 bg-white opacity-20" />
                  )}
                  {!isActive && isHovered && (
                    <span className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity text-lg">
                      {item.gesture}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer Section */}
          <div className="mt-auto space-y-4 pt-6 border-t border-gray-100 dark:border-gray-800">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="w-full flex items-center gap-4 px-3.5 py-3.5 rounded-2xl bg-gray-50 dark:bg-gray-800/50 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all border border-transparent hover:border-gray-200 dark:hover:border-gray-700 overflow-hidden"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5 flex-shrink-0" /> : <Moon className="w-5 h-5 flex-shrink-0" />}
              <motion.span
                animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : -10 }}
                className="font-semibold text-sm whitespace-nowrap"
              >
                {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              </motion.span>
            </button>

            {/* Profile Brief */}
            <div className="p-3 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/50 rounded-3xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 flex-shrink-0 rounded-full bg-[#105F68] flex items-center justify-center text-white font-bold shadow-inner">
                  UK
                </div>
                <motion.div
                  animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : -10 }}
                  className="flex-1 min-w-0"
                >
                  <p className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">Ujjwal Kumar</p>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">Level 5 Signer</p>
                </motion.div>
                {isHovered && <Settings className="w-4 h-4 flex-shrink-0 text-gray-400 hover:text-[#105F68] transition-colors cursor-pointer" />}
              </div>
            </div>
          </div>
        </div>
      </motion.aside>

      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
}
