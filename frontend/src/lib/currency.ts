/**
 * Indian currency and numerical formatting utilities.
 */

export function formatRupee(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === '') {
    return '₹0.00';
  }

  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) {
    return '₹0.00';
  }

  const isNegative = num < 0;
  const absNum = Math.abs(num);

  const formatted = absNum.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return isNegative ? `-₹${formatted}` : `₹${formatted}`;
}

export function formatPercent(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === '') {
    return '—';
  }

  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) {
    return '—';
  }

  return `${num.toFixed(2)}%`;
}

export function formatQuantity(val: string | number | null | undefined, unitName?: string): string {
  if (val === null || val === undefined || val === '') {
    return '0';
  }

  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) {
    return '0';
  }

  const cleanNum = Number.isInteger(num) ? num.toString() : num.toFixed(2).replace(/\.?0+$/, '');
  return unitName ? `${cleanNum} ${unitName}` : cleanNum;
}

export function parseNumericString(val: string | null | undefined): string {
  if (!val) return '0';
  // Strip currency symbols and whitespace
  const cleaned = val.replace(/[^0-9.-]/g, '').trim();
  return cleaned === '' ? '0' : cleaned;
}

