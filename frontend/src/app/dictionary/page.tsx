"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { Search, Filter, Camera, X } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../utils/api';
import { SignMedia } from '../components/SignMedia';
import { DictionaryWord } from '../learning/types';

const DIFFICULTY_STYLES: Record<string, string> = {
    easy: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    hard: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
};

const titleCase = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export default function DictionaryPage() {
    const router = useRouter();
    const [words, setWords] = useState<DictionaryWord[]>([]);
    const [practicable, setPracticable] = useState<Set<string>>(new Set());
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [selected, setSelected] = useState<DictionaryWord | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const [dict, vocab] = await Promise.all([api.getDictionary(), api.getVocabulary()]);
                setWords(dict.words || []);
                setPracticable(new Set(
                    (vocab.words || []).filter((w: any) => w.recognizable).map((w: any) => String(w.word).toLowerCase())
                ));
            } catch (error: any) {
                toast.error(error.message || 'Failed to load dictionary');
            } finally {
                setIsLoading(false);
            }
        })();
    }, []);

    useEffect(() => {
        if (!isLoading) {
            gsap.fromTo('.search-bar', { y: -50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' });
            gsap.fromTo('.category-filter', { y: -30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, delay: 0.1, ease: 'power3.out' });
        }
    }, [isLoading]);

    const categories = useMemo(() => ['All', ...Array.from(new Set(words.map((w) => w.category))).sort()], [words]);

    const filteredWords = useMemo(() => {
        const q = searchQuery.trim().toLowerCase();
        return words.filter((w) =>
            (selectedCategory === 'All' || w.category === selectedCategory) &&
            (!q || w.display_name.toLowerCase().includes(q) || w.word.includes(q) ||
                w.category.toLowerCase().includes(q) || w.hindi_name.includes(q))
        );
    }, [words, searchQuery, selectedCategory]);

    const canPractice = (w: DictionaryWord) => practicable.has(w.word.toLowerCase());

    return (
        <div className="min-h-screen p-6 md:p-12">
            <div className="max-w-7xl mx-auto">
                <div className="mb-12">
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                        SignVista Dictionary
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400">
                        Explore {words.length} Indian Sign Language signs with step-by-step descriptions
                    </p>
                </div>

                <div className="search-bar mb-8">
                    <div className="relative">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search for signs, words (English or Hindi), or categories..."
                            className="w-full pl-16 pr-6 py-5 rounded-2xl bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 focus:border-violet-500 outline-none text-lg shadow-lg transition-all duration-300"
                        />
                    </div>
                </div>

                <div className="category-filter mb-12">
                    <div className="flex items-center gap-3 mb-4">
                        <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        <span className="font-semibold text-gray-900 dark:text-gray-100">Categories</span>
                    </div>
                    <div className="flex flex-wrap gap-3">
                        {categories.map((category) => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 ${selectedCategory === category
                                    ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg scale-105'
                                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'}`}
                            >
                                {titleCase(category)}
                            </button>
                        ))}
                    </div>
                </div>

                {!isLoading && (
                    <div className="mb-6 text-gray-600 dark:text-gray-400">
                        Showing {filteredWords.length} {filteredWords.length === 1 ? 'sign' : 'signs'}
                    </div>
                )}

                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="w-16 h-16 border-4 border-[#344C3D] border-t-transparent rounded-full animate-spin mb-4" />
                        <p className="text-gray-600 dark:text-gray-400 font-medium">Loading signs...</p>
                    </div>
                ) : filteredWords.length === 0 ? (
                    <div className="text-center py-20">
                        <div className="text-6xl mb-4">🔍</div>
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">No signs found</h3>
                        <p className="text-gray-600 dark:text-gray-400">Try adjusting your search or filter criteria</p>
                    </div>
                ) : (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {filteredWords.map((word) => (
                            <button
                                key={word.word}
                                onClick={() => setSelected(word)}
                                className="text-left group bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300 overflow-hidden"
                            >
                                <SignMedia gifUrl={word.gif_url} label={word.display_name} className="w-full aspect-video" />
                                <div className="p-5">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{word.display_name}</h3>
                                        <span className={`text-xs px-3 py-1 rounded-full font-medium ${DIFFICULTY_STYLES[word.difficulty] ?? ''}`}>
                                            {word.difficulty}
                                        </span>
                                    </div>
                                    {word.hindi_name && <p className="text-sm text-[#105F68] dark:text-[#63C1BB] font-medium">{word.hindi_name}</p>}
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">{word.description}</p>
                                    <div className="flex items-center gap-2 mt-3">
                                        <span className="text-xs px-3 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300 rounded-full font-medium">
                                            {titleCase(word.category)}
                                        </span>
                                        {canPractice(word) && (
                                            <span className="text-xs px-3 py-1 bg-[#105F68]/10 text-[#105F68] dark:text-[#63C1BB] rounded-full font-medium flex items-center gap-1">
                                                <Camera className="w-3 h-3" /> Camera practice
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {selected && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setSelected(null)}>
                    <div
                        className="bg-white dark:bg-gray-900 rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden"
                        onClick={(e) => e.stopPropagation()}
                        role="dialog"
                        aria-modal="true"
                        aria-label={selected.display_name}
                    >
                        <div className="relative">
                            <SignMedia gifUrl={selected.gif_url} label={selected.display_name} className="w-full aspect-video" />
                            <button
                                onClick={() => setSelected(null)}
                                className="absolute top-4 right-4 p-2 rounded-full bg-white/80 dark:bg-gray-900/80"
                                aria-label="Close"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-8">
                            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                                {selected.display_name}
                                {selected.hindi_name && <span className="ml-3 text-xl text-[#105F68] dark:text-[#63C1BB]">{selected.hindi_name}</span>}
                            </h2>
                            <p className="text-gray-600 dark:text-gray-300 mt-4">{selected.description}</p>
                            {selected.tips.length > 0 && (
                                <>
                                    <h3 className="font-bold mt-6 mb-2 text-gray-900 dark:text-gray-100">Tips</h3>
                                    <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                                        {selected.tips.map((tip) => <li key={tip}>{tip}</li>)}
                                    </ul>
                                </>
                            )}
                            {canPractice(selected) ? (
                                <button
                                    onClick={() => router.push(`/learning?practice=${encodeURIComponent(selected.word)}`)}
                                    className="mt-8 w-full flex items-center justify-center gap-2 px-4 py-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold"
                                >
                                    <Camera className="w-5 h-5" /> Practice with camera
                                </button>
                            ) : (
                                <p className="mt-8 text-sm text-gray-500">
                                    Camera practice for this sign isn&apos;t available yet — our recognition model doesn&apos;t cover it.
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
