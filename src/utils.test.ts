/**
 * LIMS Utility Functions Tests
 *
 * npm run test
 * npm run test:ui
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'

// ============================================================
// getShiftDate Tests
// ============================================================

describe('getShiftDate', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('returns today for daytime hours (7:00-23:59)', () => {
    // 2026-01-11 14:00 (өдөр)
    vi.setSystemTime(new Date(2026, 0, 11, 14, 0, 0))

    const getShiftDate = () => {
      const d = new Date()
      const h = d.getHours()
      if (h < 7) {
        d.setDate(d.getDate() - 1)
      }
      return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
      )
    }

    expect(getShiftDate()).toBe('2026-01-11')
  })

  it('returns yesterday for night shift hours (0:00-6:59)', () => {
    // 2026-01-11 03:00 (шөнө) → өмнөх өдөр буцаах
    vi.setSystemTime(new Date(2026, 0, 11, 3, 0, 0))

    const getShiftDate = () => {
      const d = new Date()
      const h = d.getHours()
      if (h < 7) {
        d.setDate(d.getDate() - 1)
      }
      return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
      )
    }

    expect(getShiftDate()).toBe('2026-01-10')
  })

  it('returns today at exactly 7:00', () => {
    vi.setSystemTime(new Date(2026, 0, 11, 7, 0, 0))

    const getShiftDate = () => {
      const d = new Date()
      const h = d.getHours()
      if (h < 7) {
        d.setDate(d.getDate() - 1)
      }
      return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
      )
    }

    expect(getShiftDate()).toBe('2026-01-11')
  })

  it('returns yesterday at 6:59', () => {
    vi.setSystemTime(new Date(2026, 0, 11, 6, 59, 0))

    const getShiftDate = () => {
      const d = new Date()
      const h = d.getHours()
      if (h < 7) {
        d.setDate(d.getDate() - 1)
      }
      return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
      )
    }

    expect(getShiftDate()).toBe('2026-01-10')
  })
})

// ============================================================
// Formatting Tests
// ============================================================

describe('formatNumber', () => {
  const formatNumber = (value: number, decimals = 2): string => {
    return value.toFixed(decimals)
  }

  it('formats number with default 2 decimals', () => {
    expect(formatNumber(3.14159)).toBe('3.14')
  })

  it('formats number with custom decimals', () => {
    expect(formatNumber(3.14159, 4)).toBe('3.1416')
  })

  it('handles whole numbers', () => {
    expect(formatNumber(42)).toBe('42.00')
  })

  it('handles negative numbers', () => {
    expect(formatNumber(-5.5, 1)).toBe('-5.5')
  })
})

// ============================================================
// Validation Tests
// ============================================================

describe('isValidSampleCode', () => {
  const isValidSampleCode = (code: string): boolean => {
    // Format: ABC-2026-001 эсвэл ABC_2026_001
    const pattern = /^[A-Z]{2,5}[-_]\d{4}[-_]\d{3,5}$/
    return pattern.test(code)
  }

  it('accepts valid sample codes', () => {
    expect(isValidSampleCode('ABC-2026-001')).toBe(true)
    expect(isValidSampleCode('ER_2026_123')).toBe(true)
    expect(isValidSampleCode('LIMS-2026-00001')).toBe(true)
  })

  it('rejects invalid sample codes', () => {
    expect(isValidSampleCode('abc-2026-001')).toBe(false) // lowercase
    expect(isValidSampleCode('A-2026-001')).toBe(false) // too short
    expect(isValidSampleCode('ABC-26-001')).toBe(false) // wrong year format
    expect(isValidSampleCode('ABC2026001')).toBe(false) // no separator
  })
})

// ============================================================
// Array Utility Tests
// ============================================================

describe('groupBy', () => {
  const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
    return array.reduce(
      (result, item) => {
        const groupKey = String(item[key])
        if (!result[groupKey]) {
          result[groupKey] = []
        }
        result[groupKey].push(item)
        return result
      },
      {} as Record<string, T[]>
    )
  }

  it('groups array by key', () => {
    const samples = [
      { id: 1, status: 'new' },
      { id: 2, status: 'completed' },
      { id: 3, status: 'new' },
    ]

    const grouped = groupBy(samples, 'status')

    expect(grouped['new']).toHaveLength(2)
    expect(grouped['completed']).toHaveLength(1)
  })

  it('handles empty array', () => {
    const grouped = groupBy([], 'status' as never)
    expect(grouped).toEqual({})
  })
})
