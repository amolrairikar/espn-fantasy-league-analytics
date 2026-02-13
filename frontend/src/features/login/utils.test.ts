import { describe, test, expect } from 'vitest';
import { calculateSeasonRange } from '@/features/login/utils';

describe('calculateSeasonRange', () => {
  
  describe('Happy Path', () => {
    test('should return a range of years for valid inputs', () => {
      const result = calculateSeasonRange("2020", "2023");
      expect(result).toEqual(["2020", "2021", "2022", "2023"]);
    });

    test('should return a single year if start and end are the same', () => {
      const result = calculateSeasonRange("2024", "2024");
      expect(result).toEqual(["2024"]);
    });
  });

  describe('Validation & Constraints', () => {
    test('should return empty array if oldest or recent is missing', () => {
      expect(calculateSeasonRange(undefined, "2024")).toEqual([]);
      expect(calculateSeasonRange("2020", "")).toEqual([]);
    });

    test('should return empty array if inputs are not numeric strings', () => {
      expect(calculateSeasonRange("twenty-twenty", "2024")).toEqual([]);
      expect(calculateSeasonRange("2020", "abc")).toEqual([]);
    });

    test('should return empty array if start year is after end year', () => {
      const result = calculateSeasonRange("2024", "2020");
      expect(result).toEqual([]);
    });
  });

  describe('Max Range Safety Cap', () => {
    test('should return empty array if range exceeds default maxRange (50)', () => {
      const result = calculateSeasonRange("1900", "1960"); // Range is 60
      expect(result).toEqual([]);
    });

    test('should return empty array if range exactly equals maxRange (exclusive check)', () => {
      const result = calculateSeasonRange("2000", "2050", 50);
      expect(result).toEqual([]);
    });

    test('should respect a custom maxRange', () => {
      const result = calculateSeasonRange("2020", "2025", 3); // Range is 5
      expect(result).toEqual([]);
    });

    test('should allow large ranges if maxRange is increased', () => {
      const result = calculateSeasonRange("1900", "2000", 150);
      expect(result.length).toBe(101);
      expect(result[0]).toBe("1900");
      expect(result[100]).toBe("2000");
    });
  });

});