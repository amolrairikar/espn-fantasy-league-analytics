import type { PollOptions } from '@/features/home/types';

/**
 * Periodically executes an asynchronous function until a validation condition is met 
 * or a timeout is reached.
 * * @template T - The type of the data returned by the poll function.
 * @param {() => Promise<T>} fn - The asynchronous function to execute repeatedly.
 * @param {PollOptions<T>} options - Configuration for the polling behavior.
 * @param {number} options.interval - The delay (in milliseconds) between attempts.
 * @param {number} [options.timeout] - The maximum duration (in milliseconds) to poll before rejecting.
 * @param {(result: T) => boolean} options.validate - A predicate function that determines if the polling is successful.
 * * @returns {Promise<T>} A promise that resolves with the successful result or rejects on timeout/error.
 * @throws {Error} Rejects if the timeout is exceeded or if `fn` throws an error.
 */
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
