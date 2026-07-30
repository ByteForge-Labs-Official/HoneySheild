import { describe, it, expect } from 'vitest';
import { compactNumber } from '@/utils/format';

describe('compactNumber', () => {
  it('returns plain numbers as-is', () => {
    expect(compactNumber(0)).toBe('0');
    expect(compactNumber(42)).toBe('42');
    expect(compactNumber(999)).toBe('999');
  });
  it('formats thousands with K', () => {
    expect(compactNumber(1500)).toBe('1.5K');
    expect(compactNumber(12_300)).toBe('12.3K');
  });
  it('formats millions with M', () => {
    expect(compactNumber(1_500_000)).toBe('1.5M');
  });
});