'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Quote } from 'lucide-react';

const quotes = [
    "The barrier is never deafness. The barrier is ignorance — and ignorance can be unlearned.",
    "Sign language is the equal of speech, lending itself equally to the rigorous and the poetic.",
    "Kindness is a language which the deaf can hear and the blind can see.",
    "Listen with your eyes, speak with your hands.",
];

export function RotatingQuote() {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setIndex((prev) => (prev + 1) % quotes.length);
        }, 6000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="relative w-full max-w-3xl mx-auto flex flex-col items-center justify-center min-h-[100px] text-center px-4">
            {/* Decorative Quote Marks */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 0.3, y: 0 }}
                transition={{ duration: 1, ease: 'easeOut' }}
                className="absolute -top-4 -left-4 text-[#63C1BB]"
            >
                <Quote size={40} className="transform rotate-180" />
            </motion.div>
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 0.3, y: 0 }}
                transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
                className="absolute -bottom-4 -right-4 text-[#63C1BB]"
            >
                <Quote size={40} />
            </motion.div>

            {/* Auto-rotating Text */}
            <AnimatePresence mode="wait">
                <motion.p
                    key={index}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -15 }}
                    transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
                    className="text-lg md:text-xl italic font-medium text-[#BFCFBB] drop-shadow-sm leading-relaxed"
                >
                    "{quotes[index]}"
                </motion.p>
            </AnimatePresence>
        </div>
    );
}
