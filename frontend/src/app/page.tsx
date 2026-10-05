"use client";

import Link from 'next/link';
import { Sparkles, Activity, ShieldCheck, Heart, ArrowRight, Zap, Globe, Users } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8FAFA] dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 overflow-hidden font-sans">

      {/* Top Navigation */}
      <nav className="fixed w-full top-0 z-50 bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-[#105F68]" />
            <span className="text-2xl font-black tracking-tighter">SignVista</span>
          </div>
          <div className="hidden md:flex gap-8 font-bold text-sm tracking-wide text-gray-600 dark:text-gray-300">
            <a href="#features" className="hover:text-[#105F68] transition-colors">FEATURES</a>
            <a href="#impact" className="hover:text-[#105F68] transition-colors">WELFARE & IMPACT</a>
            <a href="#pricing" className="hover:text-[#105F68] transition-colors">PRICING</a>
          </div>
          <div className="flex gap-4">
            <Link href="/auth" className="hidden md:flex items-center justify-center px-5 py-2.5 rounded-xl font-bold text-sm border-2 border-gray-200 dark:border-gray-700 hover:border-[#105F68] transition-colors">
              Sign In
            </Link>
            <Link href="/auth" className="flex items-center justify-center px-6 py-2.5 rounded-xl font-bold text-sm bg-gradient-to-r from-[#105F68] to-[#3A9295] text-white shadow-xl hover:shadow-2xl hover:scale-105 transition-all">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-20 lg:pt-48 lg:pb-32 px-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#3A9295]/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-violet-500/10 rounded-full blur-3xl" />
        </div>

        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#3A9295]/30 bg-[#3A9295]/10 text-[#105F68] dark:text-[#63C1BB] font-bold text-sm mb-6">
            <Activity className="w-4 h-4" />
            Introducing Real-Time WebSockets for ISL
          </div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[1.1] bg-gradient-to-r from-gray-900 to-gray-500 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            The Modern Sign Language Operating System.
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed font-medium">
            Enterprise-grade AI translation meets global accessibility. Translate, learn, and connect without boundaries using our blazing-fast real-time inference engine.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            <Link href="/auth" className="w-full sm:w-auto px-8 py-4 rounded-2xl font-black text-lg bg-[#105F68] text-white shadow-2xl hover:bg-[#0c474e] hover:scale-105 transition-all flex items-center justify-center gap-2">
              Start For Free <ArrowRight className="w-5 h-5" />
            </Link>
            <a href="#pricing" className="w-full sm:w-auto px-8 py-4 rounded-2xl font-bold text-lg border-2 border-gray-200 dark:border-gray-800 bg-white dark:bg-black hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors flex items-center justify-center">
              View Pricing
            </a>
          </div>
        </div>
      </section>

      {/* Scale & Pipeline Showcase */}
      <section id="features" className="py-24 bg-white dark:bg-[#0f0f0f] border-y border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-6 space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-4xl md:text-5xl font-black tracking-tight">Built for Scale & Latency</h2>
            <p className="text-gray-500 text-lg">Our architecture guarantees seamless communication.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 rounded-[2rem] bg-[#F8FAFA] dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
              <Zap className="w-12 h-12 text-[#105F68] mb-6" />
              <h3 className="text-2xl font-bold mb-4">WebSocket Core</h3>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Sub-50ms latency for continuous real-time camera translation. No HTTP polling overhead.</p>
            </div>
            <div className="p-8 rounded-[2rem] bg-[#F8FAFA] dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
              <Globe className="w-12 h-12 text-[#3A9295] mb-6" />
              <h3 className="text-2xl font-bold mb-4">Global Network</h3>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Deployed on scalable infrastructure ensuring 99.9% uptime for enterprise and individuals globally.</p>
            </div>
            <div className="p-8 rounded-[2rem] bg-[#F8FAFA] dark:bg-gray-900 border border-gray-200 dark:border-gray-800">
              <ShieldCheck className="w-12 h-12 text-violet-500 mb-6" />
              <h3 className="text-2xl font-bold mb-4">Enterprise Grade</h3>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Stringent rate-limiting, secure authenticated WebSockets, and encrypted JWT pipelines.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center space-y-4 mb-20">
            <h2 className="text-5xl font-black tracking-tight">Transparent Pricing</h2>
            <p className="text-gray-500 text-xl font-medium">Sustainable business models balancing revenue and social impact.</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Free Tier */}
            <div className="bg-white dark:bg-gray-900 rounded-[3rem] p-10 border border-gray-200 dark:border-gray-800 flex flex-col">
              <div className="mb-8">
                <h3 className="text-3xl font-bold mb-2">Explorer</h3>
                <p className="text-gray-500">For students & casual learners</p>
              </div>
              <div className="mb-8">
                <span className="text-5xl font-black">$0</span>
                <span className="text-gray-500 font-medium">/month</span>
              </div>
              <ul className="space-y-4 mb-10 flex-1 font-medium text-gray-600 dark:text-gray-400">
                <li className="flex items-center gap-3"><ShieldCheck className="w-5 h-5 text-green-500" /> 15 mins AR translation/day</li>
                <li className="flex items-center gap-3"><ShieldCheck className="w-5 h-5 text-green-500" /> Basic Dictionary Access</li>
                <li className="flex items-center gap-3"><ShieldCheck className="w-5 h-5 text-green-500" /> Community Forums</li>
              </ul>
              <Link href="/auth" className="w-full py-4 rounded-xl font-bold bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-center">Get Started Free</Link>
            </div>

            {/* Pro Tier */}
            <div className="bg-[#105F68] text-white rounded-[3rem] p-10 shadow-2xl scale-105 relative flex flex-col transform">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-yellow-400 text-black px-6 py-2 rounded-full font-black text-sm tracking-widest uppercase">
                Most Popular
              </div>
              <div className="mb-8">
                <h3 className="text-3xl font-bold mb-2">Pro Signer</h3>
                <p className="text-white/70">For serious learners and professionals</p>
              </div>
              <div className="mb-8">
                <span className="text-5xl font-black">$9.99</span>
                <span className="text-white/70 font-medium">/month</span>
              </div>
              <ul className="space-y-4 mb-10 flex-1 font-medium text-white/90">
                <li className="flex items-center gap-3"><Sparkles className="w-5 h-5 text-yellow-400" /> Unlimited Real-Time AI Inference</li>
                <li className="flex items-center gap-3"><Sparkles className="w-5 h-5 text-yellow-400" /> Advanced Analytics & Reports</li>
                <li className="flex items-center gap-3"><Sparkles className="w-5 h-5 text-yellow-400" /> Priority Support</li>
                <li className="flex items-center gap-3"><Sparkles className="w-5 h-5 text-yellow-400" /> Custom Avatars & Settings</li>
              </ul>
              <Link href="/auth" className="w-full py-4 rounded-xl font-bold bg-white text-[#105F68] hover:bg-gray-100 transition-colors text-center shadow-xl">Upgrade to Pro</Link>
            </div>

            {/* Welfare Tier */}
            <div id="impact" className="bg-gradient-to-br from-violet-600 to-indigo-700 text-white rounded-[3rem] p-10 shadow-2xl flex flex-col relative overflow-hidden">
              <div className="absolute -right-10 -bottom-10 opacity-20">
                <Heart className="w-48 h-48" />
              </div>
              <div className="mb-8 relative z-10">
                <h3 className="text-3xl font-bold mb-2">Welfare Pass</h3>
                <p className="text-white/70">For Deaf/HoH individuals & NGOs</p>
              </div>
              <div className="mb-8 relative z-10">
                <span className="text-5xl font-black">$0</span>
                <span className="text-white/70 font-medium">/lifetime</span>
              </div>
              <ul className="space-y-4 mb-10 flex-1 font-medium text-white/90 relative z-10">
                <li className="flex items-center gap-3"><ShieldCheck className="w-5 h-5 text-green-400" /> Full Pro Features</li>
                <li className="flex items-center gap-3"><ShieldCheck className="w-5 h-5 text-green-400" /> Unlimited Access</li>
                <li className="flex items-center gap-3"><Users className="w-5 h-5 text-green-400" /> Institutional Dashboards</li>
              </ul>
              <button className="relative z-10 w-full py-4 rounded-xl font-bold bg-white/20 hover:bg-white/30 transition-colors text-center backdrop-blur-md">
                Apply for Welfare Pass
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-4xl md:text-5xl font-black mb-8">Ready to break the barrier?</h2>
          <Link href="/auth" className="inline-flex items-center justify-center px-10 py-5 rounded-2xl font-black text-xl bg-[#105F68] text-white shadow-2xl hover:scale-110 transition-transform">
            Create Your Free Account
          </Link>
        </div>
      </section>

    </div>
  );
}
