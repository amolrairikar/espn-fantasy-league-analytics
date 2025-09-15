import { useEffect, useState } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T | null) {
  const [state, setState] = useState<T | null>(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  useEffect(() => {
    if (state) localStorage.setItem(key, JSON.stringify(state));
    else localStorage.removeItem(key);
  }, [key, state]);

  return [state, setState] as const;
}
