'use client';

import { useState } from 'react';
import { Hand } from 'lucide-react';

interface SignMediaProps {
    gifUrl?: string | null;
    label: string;
    className?: string;
}

/**
 * Sign demonstration media. Shows the GIF when the backend has one,
 * otherwise a labelled placeholder (never a broken image).
 */
export function SignMedia({ gifUrl, label, className = '' }: SignMediaProps) {
    const [failed, setFailed] = useState(false);

    if (!gifUrl || failed) {
        return (
            <div
                className={`flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-[#105F68]/10 to-[#63C1BB]/10 text-[#105F68] dark:text-[#9ED5D1] ${className}`}
                role="img"
                aria-label={`${label} (demonstration not available yet)`}
            >
                <Hand className="w-8 h-8 opacity-60" />
                <span className="font-black text-lg text-center px-2 leading-tight">{label}</span>
                <span className="text-[10px] uppercase tracking-widest opacity-60">Demo coming soon</span>
            </div>
        );
    }

    return (
        // eslint-disable-next-line @next/next/no-img-element
        <img
            src={gifUrl}
            alt={`ISL sign for ${label}`}
            className={`object-cover ${className}`}
            onError={() => setFailed(true)}
            loading="lazy"
        />
    );
}
