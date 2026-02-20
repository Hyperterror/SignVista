'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Link from 'next/link';
import { ArrowRight, Zap, Sparkles } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

export default function HomePage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline();

    tl.fromTo('.hero-title', { y: 100, opacity: 0 }, { y: 0, opacity: 1, duration: 1, ease: 'power3.out' })
      .fromTo('.hero-subtitle', { y: 50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out' }, '-=0.6')
      .fromTo('.hero-cta', { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.6, ease: 'back.out(1.7)' }, '-=0.4');

    gsap.to('.float-element', {
      y: -20, duration: 2, ease: 'power1.inOut', yoyo: true, repeat: -1, stagger: 0.3
    });

    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card) => {
      gsap.fromTo(card,
        { y: 100, opacity: 0, rotateX: -15, scale: 0.9 },
        {
          y: 0, opacity: 1, rotateX: 0, scale: 1, duration: 0.8, ease: 'power3.out',
          scrollTrigger: { trigger: card, start: 'top 80%', end: 'top 50%', scrub: 1 },
        }
      );

      const cardElement = card as HTMLElement;
      cardElement.addEventListener('mouseenter', () => {
        gsap.to(card, { y: -10, scale: 1.02, boxShadow: '0 20px 60px rgba(52, 76, 61, 0.25)', duration: 0.3, ease: 'power2.out' });
      });
      cardElement.addEventListener('mouseleave', () => {
        gsap.to(card, { y: 0, scale: 1, boxShadow: '0 10px 30px rgba(52, 76, 61, 0.08)', duration: 0.3, ease: 'power2.out' });
      });
    });

    return () => { ScrollTrigger.getAll().forEach(trigger => trigger.kill()); };
  }, []);

  const features = [
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Real-time Translation",
      description: "Convert text and voice to ISL instantly with AI-powered translation",
      gradientStyle: { background: 'linear-gradient(135deg, #105F68, #344C3D)' }
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: "AI-Powered Accuracy",
      description: "Advanced AI ensures 95% accuracy in sign language conversion",
      gradientStyle: { background: 'linear-gradient(135deg, #738A6E, #3A9295)' }
    }
  ];

  const stats = [
    { value: "1000+", label: "ISL Signs" },
    { value: "50K+", label: "Users Served" },
    { value: "95%", label: "Accuracy" },
    { value: "24/7", label: "Available" }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center px-6 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-white via-[#BFCFBB]/8 to-[#C8E6E2]/10 dark:from-gray-900 dark:via-gray-900 dark:to-gray-900">
          <div className="absolute top-20 left-20 w-96 h-96 rounded-full blur-3xl animate-pulse" style={{ background: 'rgba(158, 213, 209, 0.12)' }} />
          <div className="absolute bottom-20 right-20 w-96 h-96 rounded-full blur-3xl animate-pulse" style={{ background: 'rgba(191, 207, 187, 0.12)' }} />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center">
          <div className="absolute -top-20 -left-20 text-8xl opacity-20 float-element">👋</div>
          <div className="absolute -top-10 -right-10 text-6xl opacity-20 float-element">🤟</div>
          <div className="absolute -bottom-10 left-10 text-7xl opacity-20 float-element">👍</div>

          <h1 className="hero-title text-6xl md:text-8xl font-bold mb-6 bg-clip-text text-transparent"
            style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #3A9295, #105F68)' }}
          >
            SignVista
          </h1>

          <p className="hero-subtitle text-2xl md:text-3xl text-gray-700 dark:text-gray-300 mb-4">
            Indian Sign Language, Simplified
          </p>

          <p className="hero-subtitle text-lg text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            AI-powered platform for translating text and voice into ISL gestures instantly
          </p>

          <div className="hero-cta flex flex-wrap gap-4 justify-center">
            <Link
              href="/text-to-sign"
              className="group px-8 py-4 text-white rounded-2xl font-semibold shadow-lg hover:shadow-2xl transition-all duration-300 flex items-center gap-2"
              style={{ background: 'linear-gradient(135deg, #344C3D, #105F68)' }}
            >
              Start Converting
              <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform duration-300" />
            </Link>

            <Link
              href="/voice-to-sign"
              className="px-8 py-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl font-semibold shadow-lg hover:shadow-2xl transition-all duration-300 border-2"
              style={{ borderColor: '#9ED5D1' }}
            >
              Voice to Sign
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
            {stats.map((stat, index) => (
              <div key={index} className="stat-card p-6 rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-lg">
                <div className="text-4xl font-bold bg-clip-text text-transparent"
                  style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #3A9295)' }}
                >
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className="py-20 px-6 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold mb-4 bg-clip-text text-transparent"
              style={{ backgroundImage: 'linear-gradient(to right, #344C3D, #105F68)' }}
            >
              Powerful Features
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Everything you need for Indian Sign Language translation
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="feature-card relative p-8 rounded-3xl bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden group cursor-pointer"
                style={{ perspective: '1000px', transformStyle: 'preserve-3d' }}
              >
                {/* Gradient overlay */}
                <div className="absolute top-0 right-0 w-32 h-32 opacity-10 rounded-bl-full" style={feature.gradientStyle} />

                {/* Icon */}
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300" style={feature.gradientStyle}>
                  {feature.icon}
                </div>

                <h3 className="text-2xl font-bold mb-3 text-gray-900 dark:text-gray-100">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{feature.description}</p>

                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <Sparkles className="w-6 h-6" style={{ color: '#63C1BB' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #105F68, #3A9295, #344C3D)' }}
      >
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 text-9xl">👋</div>
          <div className="absolute bottom-10 right-10 text-9xl">🤟</div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-9xl">✌️</div>
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center text-white">
          <h2 className="text-5xl font-bold mb-6">Ready to Start Your ISL Journey?</h2>
          <p className="text-xl mb-8 opacity-90">
            Make communication accessible for everyone with AI-powered ISL translation
          </p>
          <Link
            href="/text-to-sign"
            className="inline-flex items-center gap-2 px-10 py-5 bg-white rounded-2xl font-bold text-lg shadow-2xl hover:scale-105 transition-transform duration-300"
            style={{ color: '#344C3D' }}
          >
            Get Started Free
            <ArrowRight className="w-6 h-6" />
          </Link>
        </div>
      </section>
    </div>
  );
}
