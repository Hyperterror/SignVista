"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { SignMedia } from "../SignMedia";
import { AG_EASE, DictionaryWord } from "../../learning/types";

export function DictionaryPanel({ words, onPractice }: { words: DictionaryWord[]; onPractice: (word: string) => void }) {
    const [query, setQuery] = useState("");
    const [selected, setSelected] = useState<DictionaryWord | null>(null);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return words.filter((w) =>
            w.category !== "alphabet" &&
            (!q || w.display_name.toLowerCase().includes(q) || w.word.includes(q) || w.hindi_name.includes(q))
        );
    }, [words, query]);

    return (
        <div className="w-full flex flex-col gap-6 py-4">
            <div className="relative max-w-xl w-full mx-auto">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search signs (English or Hindi)..."
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm outline-none focus:ring-2 focus:ring-[#63C1BB]/40"
                />
            </div>

            {filtered.length === 0 && <p className="text-center text-gray-500">No signs match your search.</p>}

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
                {filtered.map((w, idx) => (
                    <motion.button
                        key={w.word}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: Math.min(idx * 0.03, 0.4), ease: AG_EASE }}
                        whileHover={{ y: -4 }}
                        onClick={() => setSelected(w)}
                        className="text-left bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 overflow-hidden shadow-md"
                    >
                        <SignMedia gifUrl={w.gif_url} label={w.display_name} className="w-full aspect-square" />
                        <div className="p-4">
                            <p className="font-black text-gray-900 dark:text-gray-100">{w.display_name}</p>
                            <p className="text-xs text-gray-500 capitalize">{w.category} · {w.difficulty}</p>
                        </div>
                    </motion.button>
                ))}
            </div>

            {selected && (
                <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setSelected(null)}>
                    <div
                        className="bg-white dark:bg-gray-900 rounded-[32px] max-w-lg w-full p-8 shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                        role="dialog"
                        aria-modal="true"
                        aria-label={selected.display_name}
                    >
                        <SignMedia gifUrl={selected.gif_url} label={selected.display_name} className="w-full aspect-video rounded-2xl mb-6" />
                        <h3 className="text-3xl font-black text-gray-900 dark:text-gray-100">
                            {selected.display_name} {selected.hindi_name && <span className="text-xl text-gray-400 font-bold">· {selected.hindi_name}</span>}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-300 mt-3">{selected.description}</p>
                        {selected.tips.length > 0 && (
                            <ul className="mt-4 space-y-1 list-disc list-inside text-sm text-gray-500">
                                {selected.tips.map((t) => <li key={t}>{t}</li>)}
                            </ul>
                        )}
                        <div className="flex gap-3 mt-8">
                            <button onClick={() => setSelected(null)} className="flex-1 py-3 rounded-xl font-bold bg-gray-100 dark:bg-gray-800">Close</button>
                            <button
                                onClick={() => { onPractice(selected.word); setSelected(null); }}
                                className="flex-1 py-3 rounded-xl font-bold bg-[#105F68] text-white"
                            >
                                Practice this sign
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
