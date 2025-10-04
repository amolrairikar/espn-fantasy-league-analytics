import type { PollOptions } from '@/features/home/types';

async function poll<T>(fn: () => Promise<T>, options: PollOptions<T>): Promise<T> {
  const { interval, timeout, validate } = options;

  const startTime = Date.now();

  return new Promise<T>((resolve, reject) => {
    const attempt = async () => {
      try {
        const result = await fn();
        if (validate(result)) {
          resolve(result);
        } else if (timeout && Date.now() - startTime >= timeout) {
          reject(new Error('Polling timed out'));
        } else {
          setTimeout(() => void attempt(), interval);
        }
      } catch (err) {
        reject(err instanceof Error ? err : new Error(String(err)));
      }
    };

    void attempt();
  });
}

export { poll };
