import { useCallback, useSyncExternalStore } from 'react';

/** Subscribes to a CSS media query. Returns `serverValue` during server rendering. */
export function useMediaQuery(query: string, serverValue = false): boolean {
    const subscribe = useCallback((onChange: () => void) => {
        const mq = window.matchMedia(query);
        mq.addEventListener('change', onChange);
        return () => mq.removeEventListener('change', onChange);
    }, [query]);

    return useSyncExternalStore(
        subscribe,
        () => window.matchMedia(query).matches,
        () => serverValue,
    );
}
