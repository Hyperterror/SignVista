export interface DictionaryWord {
    word: string;
    display_name: string;
    hindi_name: string;
    category: string;
    difficulty: string;
    gif_url: string;
    description: string;
    tips: string[];
}

export interface ProgressWord {
    word: string;
    display_name: string;
    proficiency: number;
    attempts: number;
    correct: number;
    mastery_tier: string;
}

export interface VocabularyWord {
    word: string;
    display_name: string;
    recognizable: boolean;
}

export const prettyWord = (w: string) =>
    w.length <= 2 ? w.toUpperCase() : w.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export const AG_EASE = [0.34, 1.56, 0.64, 1] as [number, number, number, number];
