/**
 * Generates an array of year strings between two boundaries.
 * @param oldest - The starting year (e.g., "2020")
 * @param recent - The ending year (e.g., "2024")
 * @param maxRange - Safety cap to prevent infinite loops or UI crashes (default 50)
 * @returns Array of strings ["2020", "2021", ...] or empty array if invalid
 */
export const calculateSeasonRange = (
  oldest?: string, 
  recent?: string, 
  maxRange: number = 50
): string[] => {
  if (!oldest || !recent) return [];

  const start = parseInt(oldest, 10);
  const end = parseInt(recent, 10);

  // Validation: Must be numbers, start must be before end, and within maxRange
  if (
    isNaN(start) || 
    isNaN(end) || 
    start > end || 
    (end - start) >= maxRange
  ) {
    return [];
  }

  return Array.from(
    { length: end - start + 1 }, 
    (_, i) => (start + i).toString()
  );
};