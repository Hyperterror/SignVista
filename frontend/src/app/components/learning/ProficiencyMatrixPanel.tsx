"use client";

import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { AG_EASE, DictionaryWord, ProgressWord } from "../../learning/types";

export function ProficiencyMatrixPanel({
    progress,
    dictionary,
    onPractice,
}: {
    progress: ProgressWord[];
    dictionary: DictionaryWord[];
    onPractice: (word: string) => void;
}) {
    const categoryOf = (word: string) => {
        const entry = dictionary.find((d) => d.word === word.toLowerCase());
        if (entry) return entry.category.charAt(0).toUpperCase() + entry.category.slice(1);
        return word.length <= 2 ? "Letters & Numbers" : "Common";
    };

    // Average proficiency per category over the signs you can practice
    const byCategory = progress.reduce<Record<string, { total: number; count: number }>>((acc, w) => {
        const cat = categoryOf(w.word);
        acc[cat] = acc[cat] || { total: 0, count: 0 };
        acc[cat].total += w.proficiency;
        acc[cat].count += 1;
        return acc;
    }, {});
    const radarData = Object.entries(byCategory).map(([area, v]) => ({ area, score: Math.round(v.total / v.count) }));

    const practiced = progress.filter((w) => w.attempts > 0).sort((a, b) => a.proficiency - b.proficiency);

    if (progress.length === 0) {
        return <p className="text-center text-gray-500 py-12">No practicable signs are available right now.</p>;
    }

    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-5xl flex flex-col md:flex-row gap-8">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.2, ease: AG_EASE }}
                    className="w-full md:w-1/2 min-h-[400px] bg-white dark:bg-gray-800/80 rounded-[24px] border border-gray-100 dark:border-gray-700 p-6 flex flex-col shadow-xl"
                >
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Skill Map</h3>
                    <p className="text-xs text-gray-500 mb-4">Average proficiency per category</p>
                    {radarData.length >= 3 ? (
                        <div className="w-full h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                                    <PolarGrid stroke="#63C1BB" strokeOpacity={0.2} />
                                    <PolarAngleAxis dataKey="area" tick={{ fill: 'currentColor', fontSize: 12, fontWeight: 600 }} />
                                    <Radar name="Proficiency" dataKey="score" stroke="#63C1BB" strokeWidth={3} fill="#63C1BB" fillOpacity={0.3} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col gap-3 justify-center">
                            {radarData.map((d) => (
                                <div key={d.area} className="flex justify-between font-bold">
                                    <span>{d.area}</span><span className="text-[#63C1BB]">{d.score}%</span>
                                </div>
                            ))}
                        </div>
                    )}
                </motion.div>

                <div className="w-full md:w-1/2 flex flex-col gap-4">
                    {practiced.length === 0 && (
                        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 text-gray-500 border border-gray-100 dark:border-gray-700">
                            You haven&apos;t practiced any signs yet. Open the Practice tab to get started.
                        </div>
                    )}
                    {practiced.slice(0, 8).map((w, idx) => {
                        const isWeak = w.proficiency < 50;
                        return (
                            <motion.button
                                key={w.word}
                                onClick={() => onPractice(w.word)}
                                initial={{ opacity: 0, x: 30 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.8, delay: 0.4 + idx * 0.08, ease: AG_EASE }}
                                className="text-left bg-white dark:bg-gray-800/60 rounded-2xl border border-gray-100 dark:border-gray-700 p-5 shadow-md hover:shadow-lg transition-all"
                            >
                                <div className="flex justify-between items-end mb-2">
                                    <span className="font-extrabold text-gray-900 dark:text-gray-100">{w.display_name}</span>
                                    <span className={`text-sm font-black ${isWeak ? 'text-red-500' : 'text-[#63C1BB]'}`}>
                                        {Math.round(w.proficiency)}% · {w.mastery_tier}
                                    </span>
                                </div>
                                <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-900 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${w.proficiency}%` }}
                                        transition={{ duration: 1.2, delay: 0.6 + idx * 0.08, ease: AG_EASE }}
                                        className={`h-full rounded-full ${isWeak ? 'bg-red-400' : 'bg-[#63C1BB]'}`}
                                    />
                                </div>
                                <p className="text-xs text-gray-500 mt-2">
                                    {w.correct}/{w.attempts} correct{isWeak ? ' · focus area — tap to practice' : ''}
                                </p>
                            </motion.button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
