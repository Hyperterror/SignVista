"use client";

import { motion } from "framer-motion";
import { Search } from "lucide-react";

const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];

// Dummy data for the dictionary grid
const DICTIONARY_ITEMS = [
    { id: 1, word: "Hello", description: "Standard greeting in ISL", category: "Greeting", gif: "👋" },
    { id: 2, word: "Thank You", description: "Expressing gratitude", category: "Daily Use", gif: "🙏" },
    { id: 3, word: "Help", description: "Asking for assistance", category: "Emergency", gif: "🆘" },
    { id: 4, word: "Please", description: "Polite request", category: "Daily Use", gif: "🥺" },
    { id: 5, word: "Sorry", description: "Apologizing", category: "Daily Use", gif: "😔" },
    { id: 6, word: "Yes", description: "Affirmative response", category: "Daily Use", gif: "👍" },
    { id: 7, word: "No", description: "Negative response", category: "Daily Use", gif: "👎" },
    { id: 8, word: "Water", description: "Requesting a drink", category: "Daily Use", gif: "💧" },
];

export function DictionaryPanel() {
    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-6xl flex flex-col items-center">

                {/* Search Bar */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2, ease: AG_EASE }}
                    className="w-full relative max-w-3xl mb-12 group"
                >
                    <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-[#63C1BB] group-focus-within:text-[#3A9295] transition-colors duration-300" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search a sign..."
                        className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full py-4 pl-14 pr-6 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-lg outline-none transition-all duration-300 focus:border-[#63C1BB] focus:ring-2 focus:ring-[#63C1BB]/20"
                    />
                </motion.div>

                {/* Dictionary Card Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
                    {DICTIONARY_ITEMS.map((item, idx) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.4 + idx * 0.06, ease: AG_EASE }}
                            whileHover={{
                                y: -8,
                                boxShadow: "0 16px 40px rgba(16, 95, 104, 0.15)",
                                borderColor: "#63C1BB",
                                transition: { duration: 0.3, ease: AG_EASE },
                            }}
                            className="bg-white dark:bg-gray-800/80 backdrop-blur-md border border-gray-200 dark:border-gray-700 rounded-2xl overflow-hidden flex flex-col group cursor-pointer"
                        >
                            {/* Top: GIF/Illustration Area */}
                            <div className="h-40 w-full bg-gray-50 dark:bg-gray-900/40 flex items-center justify-center relative overflow-hidden">
                                <span className="text-6xl group-hover:scale-110 transition-transform duration-500 ease-in-out">
                                    {item.gif}
                                </span>
                                <div className="absolute inset-0 bg-gradient-to-t from-gray-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                            </div>

                            {/* Bottom: Content Area */}
                            <div className="p-5 flex flex-col flex-1 relative bg-white/50 dark:bg-gray-800/20">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{item.word}</h3>
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#63C1BB]/10 text-[#105F68] dark:text-[#63C1BB] whitespace-nowrap">
                                        {item.category}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                                    {item.description}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
