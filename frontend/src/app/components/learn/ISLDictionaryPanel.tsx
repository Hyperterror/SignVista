'use client';

import { motion } from 'framer-motion';
import { Search } from 'lucide-react';

const mockWords = [
    { id: 1, word: 'Hello', description: 'Basic greeting bringing hand to forehead and away.' },
    { id: 2, word: 'Thank You', description: 'Fingertips to chin and move hand forward.' },
    { id: 3, word: 'Please', description: 'Flat hand rubbing chest in circular motion.' },
    { id: 4, word: 'Yes', description: 'Fist bobbing up and down simulating a head nod.' },
    { id: 5, word: 'No', description: 'Index and middle fingers tapping thumb.' },
    { id: 6, word: 'Help', description: 'Closed fist resting on flat palm moving upwards.' },
    { id: 7, word: 'Emergency', description: 'Shaking hand rapidly side to side.' },
    { id: 8, word: 'Water', description: 'W-shape fingers tapping the chin.' },
];

const easeBounce: [number, number, number, number] = [0.34, 1.56, 0.64, 1];

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.06 // 60ms stagger delay as requested
        }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: easeBounce } }
};

export function ISLDictionaryPanel() {
    return (
        <div className="w-full h-full flex flex-col">
            {/* Search Bar */}
            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6, ease: easeBounce }}
                className="mb-8 w-full max-w-md mx-auto relative group"
            >
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Search size={18} className="text-[#8EA58C] group-focus-within:text-[#9ED5D1] transition-colors" />
                </div>
                <input
                    type="text"
                    placeholder="Search a sign..."
                    className="w-full bg-[#105F68] border border-transparent text-white placeholder-[#8EA58C] rounded-full py-3 pl-11 pr-6 outline-none focus:border-[#63C1BB] focus:shadow-[0_0_15px_#63C1BB] transition-all duration-300"
                />
            </motion.div>

            {/* Dictionary Grid */}
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pb-20"
            >
                {mockWords.map((word) => (
                    <motion.div
                        key={word.id}
                        variants={itemVariants}
                        whileHover={{ translateY: -8 }}
                        className="group relative bg-[#3A9295]/20 backdrop-blur-md border border-[#63C1BB]/40 rounded-2xl p-5 cursor-pointer hover:border-[#9ED5D1] transition-colors duration-300 shadow-[0_8px_30px_rgba(16,95,104,0.1)] hover:shadow-[0_15px_35px_rgba(99,193,187,0.3)]"
                    >
                        {/* Hover Glow Edge inside border */}
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-t from-[#9ED5D1]/0 to-[#9ED5D1]/0 group-hover:from-[#9ED5D1]/10 pointer-events-none transition-all duration-300" />

                        {/* Placeholder for GIF / Illustration */}
                        <div className="w-full aspect-square bg-[#105F68]/30 rounded-xl mb-4 flex items-center justify-center border border-[#63C1BB]/20 overflow-hidden relative">
                            <div className="w-16 h-16 rounded-full bg-white/5 animate-pulse" />
                            <span className="absolute text-xs text-[#8EA58C]/50 font-medium">Video/GIF Area</span>
                        </div>

                        <h3 className="text-white font-bold text-lg mb-1">{word.word}</h3>
                        <p className="text-[#C8E6E2] text-sm leading-snug">{word.description}</p>
                    </motion.div>
                ))}
            </motion.div>
        </div>
    );
}
