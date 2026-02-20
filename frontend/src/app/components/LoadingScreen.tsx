'use client';

import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export function LoadingScreen() {
  const containerRef = useRef<HTMLDivElement>(null);
  const handRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline();

    // Animate hand morphing into logo
    tl.fromTo(
      handRef.current,
      { scale: 0, rotation: -180, opacity: 0 },
      { scale: 1.2, rotation: 0, opacity: 1, duration: 0.8, ease: 'back.out(1.7)' }
    )
      .to(handRef.current, {
        scale: 0.9,
        y: -20,
        duration: 0.4,
        ease: 'power2.inOut'
      })
      .to(handRef.current, {
        opacity: 0,
        scale: 0.5,
        duration: 0.3
      })
      .fromTo(
        logoRef.current,
        { opacity: 0, scale: 0.5, y: 20 },
        { opacity: 1, scale: 1, y: 0, duration: 0.5, ease: 'back.out(1.7)' },
        '-=0.2'
      )
      .to(containerRef.current, {
        opacity: 0,
        duration: 0.5,
        delay: 0.3
      });
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: 'linear-gradient(135deg, #105F68, #3A9295, #344C3D)' }}
    >
      <div className="relative">
        {/* Hand icon morphing */}
        <div ref={handRef} className="absolute inset-0 flex items-center justify-center">
          <div className="text-9xl">👋</div>
        </div>

        {/* Logo appearing */}
        <div ref={logoRef} className="opacity-0 text-center">
          <h1 className="text-6xl font-bold text-white mb-2">SignVista</h1>
          <p className="text-white/80 text-lg">Indian Sign Language Platform</p>
        </div>
      </div>
    </div>
  );
}
