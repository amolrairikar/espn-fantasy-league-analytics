import { useEffect, useState } from 'react';

function safeJSONParse<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

export function useLocalStorage<T>(key: string, initialValue: T | null) {
  const [state, setState] = useState<T | null>(() => {
    const stored = localStorage.getItem(key);
    return stored ? safeJSONParse<T>(stored, initialValue ?? ({} as T)) : initialValue;
  });

  useEffect(() => {
    if (state !== null) localStorage.setItem(key, JSON.stringify(state));
    else localStorage.removeItem(key);
  }, [key, state]);

  return [state, setState] as const;
}
