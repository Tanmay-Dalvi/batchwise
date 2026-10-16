import { describe, it, expect } from 'vitest';
import { formatRupee, formatPercent, parseNumericString } from '../lib/currency';

describe('currency and percentage formatting', () => {
  it('formats whole number rupees correctly', () => {
    expect(formatRupee('600')).toBe('₹600.00');
    expect(formatRupee(600)).toBe('₹600.00');
    expect(formatRupee('0')).toBe('₹0.00');
  });

  it('formats decimals with two places and Indian comma grouping', () => {
    expect(formatRupee('1875.50')).toBe('₹1,875.50');
    expect(formatRupee('100000')).toBe('₹1,00,000.00');
  });

  it('handles negative values gracefully', () => {
    expect(formatRupee('-150.25')).toBe('-₹150.25');
  });

  it('handles null, undefined, or empty values with fallback', () => {
    expect(formatRupee(null)).toBe('₹0.00');
    expect(formatRupee(undefined)).toBe('₹0.00');
    expect(formatRupee('')).toBe('₹0.00');
    expect(formatRupee('invalid')).toBe('₹0.00');
  });

  it('formats percentages correctly', () => {
    expect(formatPercent(54.1333)).toBe('54.13%');
    expect(formatPercent('118.02')).toBe('118.02%');
    expect(formatPercent(0)).toBe('0.00%');
    expect(formatPercent(null)).toBe('—');
  });

  it('parses numeric strings safely', () => {
    expect(parseNumericString(' ₹ 1,875.50 ')).toBe('1875.50');
    expect(parseNumericString('600')).toBe('600');
    expect(parseNumericString('')).toBe('0');
  });
});
