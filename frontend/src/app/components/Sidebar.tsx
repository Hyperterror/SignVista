'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import gsap from 'gsap';
import {
  Home,
  MessageSquare,
  Mic,
  Sun,
  Moon,
  Hand,
  Menu,
  X
} from 'lucide-react';

export function Sidebar() {
  const { theme, toggleTheme } = useTheme();
  const greetingRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Typing effect for greeting
    if (greetingRef.current) {
      const text = "Hey, Explorer!";
      const chars = text.split('');
      greetingRef.current.innerHTML = '';

      chars.forEach((char, i) => {
        const span = document.createElement('span');
        span.textContent = char;
        span.style.opacity = '0';
        greetingRef.current?.appendChild(span);

        gsap.to(span, {
          opacity: 1,
          duration: 0.1,
          delay: i * 0.05,
          ease: 'power1.out'
        });
      });
    }
  }, []);

  useEffect(() => {
    // Subtle parallax effect on scroll
    const handleScroll = () => {
      if (sidebarRef.current) {
        const scrollY = window.scrollY;
        gsap.to(sidebarRef.current, {
          y: scrollY * 0.1,
          duration: 0.5,
          ease: 'power2.out'
        });
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { path: '/', icon: Home, label: 'Home', gesture: '🏠' },
    { path: '/text-to-sign', icon: MessageSquare, label: 'Text → Sign', gesture: '✍️' },
    { path: '/voice-to-sign', icon: Mic, label: 'Voice → Sign', gesture: '🎤' },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white dark:bg-gray-800 shadow-lg"
      >
        {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={`
          fixed top-0 left-0 h-screen w-[280px] lg:w-[20%] 
          bg-gradient-to-b from-white via-[#BFCFBB]/10 to-[#C8E6E2]/15 dark:from-gray-900 dark:to-gray-800
          border-r border-gray-200 dark:border-gray-700
          px-6 py-8 overflow-y-auto z-40
          transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          shadow-2xl lg:shadow-none
        `}
        style={{
          boxShadow: '4px 0 24px rgba(52, 76, 61, 0.08)'
        }}
      >
        {/* Logo & Greeting */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-300"
              style={{ background: 'linear-gradient(135deg, #344C3D, #105F68)' }}
            >
              <Hand className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-clip-text text-transparent"
                style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #3A9295)' }}
              >
                SignVista
              </h1>
              <p className="text-xs text-gray-600 dark:text-gray-400">ISL Platform</p>
            </div>
          </div>

          <div
            ref={greetingRef}
            className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2"
          >
            Hey, Explorer!
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Translate with sign language
          </p>
        </div>

        {/* Navigation */}
        <nav className="space-y-2 mb-12">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;

            return (
              <Link
                key={item.path}
                href={item.path}
                onClick={() => setIsMobileOpen(false)}
                className={`
                  nav-link group relative flex items-center gap-3 px-4 py-3 rounded-xl
                  transition-all duration-300 overflow-hidden
                  ${isActive
                    ? 'text-white shadow-lg scale-105'
                    : 'hover:bg-[#C8E6E2]/30 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300'
                  }
                `}
                style={isActive ? { background: 'linear-gradient(135deg, #344C3D, #105F68)' } : undefined}
              >
                {/* Pulsing glow for active state */}
                {isActive && (
                  <div className="absolute inset-0 opacity-20 animate-pulse"
                    style={{ background: 'linear-gradient(135deg, #9ED5D1, #BFCFBB)' }}
                  />
                )}

                {/* Icon morphs to gesture on hover */}
                <span className="relative z-10 group-hover:scale-110 transition-transform duration-300">
                  <span className="group-hover:hidden inline-block">
                    <Icon size={20} />
                  </span>
                  <span className="hidden group-hover:inline-block text-xl">
                    {item.gesture}
                  </span>
                </span>

                <span className="relative z-10 font-medium">{item.label}</span>

                {/* Highlight bar */}
                {isActive && (
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-l-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Theme Toggle */}
        <div className="mt-auto pt-8 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-white/50 dark:bg-gray-700/50 hover:bg-white dark:hover:bg-gray-700 transition-all duration-300 group"
          >
            <span className="text-sm font-medium">Theme</span>
            <div className="relative w-12 h-6 bg-gray-300 dark:bg-gray-600 rounded-full transition-colors duration-300">
              <div className={`
                absolute top-1 w-4 h-4 rounded-full bg-white shadow-md
                transition-transform duration-300 flex items-center justify-center
                ${theme === 'dark' ? 'translate-x-7' : 'translate-x-1'}
              `}>
                {theme === 'dark' ? <Moon size={10} /> : <Sun size={10} />}
              </div>
            </div>
          </button>
        </div>

        {/* Floating decoration */}
        <div className="absolute bottom-20 right-6 text-6xl opacity-10 pointer-events-none animate-pulse">
          👋
        </div>
      </aside>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen(false)}
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
        />
      )}
    </>
  );
}
