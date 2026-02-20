'use client';

import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

// Generates random particles
export function FloatingParticles() {
    const [particles, setParticles] = useState<Array<{ id: number; top: string; left: string; size: number; duration: number; delay: number }>>([]);

    useEffect(() => {
        // We only generate random positions on the client to avoid hydration mismatch
        const newParticles = Array.from({ length: 40 }).map((_, i) => ({
            id: i,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            size: Math.random() * 4 + 2, // 2px to 6px
            duration: Math.random() * 20 + 20, // 20s to 40s float time
            delay: Math.random() * -20, // Start at different times
        }));
        setParticles(newParticles);
    }, []);

    return (
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
            {particles.map((p) => (
                <motion.div
                    key={p.id}
                    className="absolute rounded-full bg-[#63C1BB]/10"
                    style={{
                        top: p.top,
                        left: p.left,
                        width: p.size,
                        height: p.size,
                    }}
                    animate={{
                        y: ['0vh', '-100vh'],
                        x: ['0vw', `${Math.random() * 10 - 5}vw`], // Drifting left/right slightly
                        opacity: [0, 1, 1, 0]
                    }}
                    transition={{
                        duration: p.duration,
                        repeat: Infinity,
                        ease: 'linear',
                        delay: p.delay,
                    }}
                />
            ))}
        </div>
    );
}
