'use client';

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore, ReactNode } from 'react';

type Theme = 'light' | 'dark';
export type ThemePreference = Theme | 'system';

interface ThemeContextType {
  /** The theme currently applied */
  theme: Theme;
  /** What the user chose (may be "system") */
  preference: ThemePreference;
  setPreference: (pref: ThemePreference) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
const STORAGE_KEY = 'signvista-theme';
const CHANGE_EVENT = 'signvista-theme-change';
const DEFAULT_PREFERENCE: ThemePreference = 'dark';

// ── Stored preference (localStorage, synced across tabs) ──
function readPreference(): ThemePreference {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === 'light' || saved === 'dark' || saved === 'system' ? saved : DEFAULT_PREFERENCE;
  } catch {
    return DEFAULT_PREFERENCE;
  }
}

function subscribePreference(onChange: () => void) {
  window.addEventListener('storage', onChange);
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => {
    window.removeEventListener('storage', onChange);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}

// ── OS colour scheme ──
const LIGHT_QUERY = '(prefers-color-scheme: light)';

function readSystemTheme(): Theme {
  return window.matchMedia?.(LIGHT_QUERY).matches ? 'light' : 'dark';
}

function subscribeSystemTheme(onChange: () => void) {
  const mq = window.matchMedia?.(LIGHT_QUERY);
  mq?.addEventListener('change', onChange);
  return () => mq?.removeEventListener('change', onChange);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const preference = useSyncExternalStore(subscribePreference, readPreference, () => DEFAULT_PREFERENCE);
  const systemTheme = useSyncExternalStore(subscribeSystemTheme, readSystemTheme, () => 'dark' as Theme);
  const theme: Theme = preference === 'system' ? systemTheme : preference;

  // Sync the <html> class (an external system) with the resolved theme
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const setPreference = useCallback((pref: ThemePreference) => {
    try {
      localStorage.setItem(STORAGE_KEY, pref);
    } catch {
      // storage unavailable (private mode); the change still applies for this page
    }
    window.dispatchEvent(new Event(CHANGE_EVENT));
  }, []);

  const toggleTheme = useCallback(() => setPreference(theme === 'dark' ? 'light' : 'dark'), [theme, setPreference]);

  return (
    <ThemeContext.Provider value={{ theme, preference, setPreference, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
