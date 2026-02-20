"use client";

import { motion } from "framer-motion";
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    ResponsiveContainer,
} from "recharts";

const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];

const MOCK_DATA = [
    { area: "Greetings", score: 85 },
    { area: "Emergency", score: 40 },
    { area: "Numbers", score: 92 },
    { area: "Emotions", score: 65 },
    { area: "Daily Use", score: 78 },
];

export function ProficiencyMatrixPanel() {
    return (
        <div className="w-full flex justify-center py-4">
            <div className="w-full max-w-5xl flex flex-col md:flex-row gap-8">

                {/* Radar Chart Container */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8, delay: 0.2, ease: AG_EASE }}
                    className="w-full md:w-1/2 min-h-[400px] bg-white dark:bg-gray-800/80 backdrop-blur-md rounded-[24px] border border-gray-100 dark:border-gray-700 p-6 flex flex-col items-center justify-center relative shadow-xl"
                >
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6 absolute top-6 left-6">Skill Map</h3>

                    <div className="w-full h-[300px] mt-8">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={MOCK_DATA}>
                                <PolarGrid stroke="#63C1BB" strokeOpacity={0.2} />
                                <PolarAngleAxis
                                    dataKey="area"
                                    tick={{ fill: 'currentColor', className: 'text-gray-500 dark:text-gray-400', fontSize: 12, fontWeight: 600 }}
                                />
                                <Radar
                                    name="Proficiency"
                                    dataKey="score"
                                    stroke="#63C1BB"
                                    strokeWidth={3}
                                    fill="#63C1BB"
                                    fillOpacity={0.3}
                                />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Skill Bars Container */}
                <div className="w-full md:w-1/2 flex flex-col gap-4">
                    {MOCK_DATA.map((skill, idx) => {
                        const isWeak = skill.score < 50;
                        return (
                            <motion.div
                                key={skill.area}
                                initial={{ opacity: 0, x: 30 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ duration: 0.8, delay: 0.4 + idx * 0.1, ease: AG_EASE }}
                                className="bg-white dark:bg-gray-800/60 backdrop-blur-sm rounded-2xl border border-gray-100 dark:border-gray-700 p-5 flex flex-col justify-center shadow-md hover:shadow-lg transition-all"
                            >
                                <div className="flex justify-between items-end mb-2">
                                    <span className="font-extrabold text-gray-900 dark:text-gray-100">{skill.area}</span>
                                    <span className={`text-sm font-black ${isWeak ? 'text-red-500' : 'text-[#63C1BB]'}`}>
                                        {skill.score}%
                                    </span>
                                </div>

                                <div className="w-full h-2.5 bg-gray-100 dark:bg-gray-900 rounded-full overflow-hidden relative">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${skill.score}%` }}
                                        transition={{ duration: 1.2, delay: 0.6 + idx * 0.1, ease: AG_EASE }}
                                        className={`h-full rounded-full ${isWeak ? 'bg-red-400' : 'bg-[#63C1BB]'}`}
                                    />
                                </div>

                                {isWeak && (
                                    <p className="text-[10px] uppercase tracking-widest font-black text-red-500 mt-3">
                                        Focus area recommended
                                    </p>
                                )}
                            </motion.div>
                        );
                    })}
                </div>

            </div>
        </div>
    );
}
