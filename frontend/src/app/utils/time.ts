import { useSyncExternalStore } from 'react';

/** Current time in Unix seconds (for event handlers and effects, not render). */
export const nowSeconds = () => Date.now() / 1000;

// A shared, minute-resolution clock so relative times ("5m ago") stay pure during render.
let currentNow = 0;
const listeners = new Set<() => void>();
let timer: ReturnType<typeof setInterval> | null = null;

function subscribe(listener: () => void) {
    listeners.add(listener);
    if (!timer) {
        currentNow = nowSeconds();
        timer = setInterval(() => {
            currentNow = nowSeconds();
            listeners.forEach((l) => l());
        }, 30_000);
    }
    return () => {
        listeners.delete(listener);
        if (listeners.size === 0 && timer) {
            clearInterval(timer);
            timer = null;
        }
    };
}

/** Unix seconds, refreshed every 30s. Returns 0 during server rendering. */
export function useNow(): number {
    return useSyncExternalStore(
        subscribe,
        () => currentNow || (currentNow = nowSeconds()),
        () => 0,
    );
}

export function formatRelative(timestamp: number, now: number): string {
    if (!now) return '';
    const diff = Math.max(0, now - timestamp);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}
