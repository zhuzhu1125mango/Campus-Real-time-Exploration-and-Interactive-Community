import { describe, expect, it } from 'vitest'

import { formatDate, formatDateTime, formatTime } from '../date'

describe('date utils', () => {
  it('returns empty string for empty or invalid input', () => {
    expect(formatTime('')).toBe('')
    expect(formatDateTime('')).toBe('')
    expect(formatDate('')).toBe('')
    expect(formatTime('not-a-date')).toBe('')
    expect(formatDateTime('not-a-date')).toBe('')
  })

  it('formats date time as YYYY-MM-DD HH:mm', () => {
    const date = new Date(2026, 0, 5, 8, 7)
    expect(formatDateTime(date)).toBe('2026-01-05 08:07')
  })

  it('formats same-day time as HH:mm', () => {
    const now = new Date()
    const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 9, 5)
    expect(formatTime(date)).toBe('09:05')
  })

  it('formats other days in the same year as MM-DD', () => {
    const now = new Date()
    const date = new Date(now.getFullYear(), 0, 2, 10, 0)
    if (now.getMonth() === 0 && now.getDate() === 2) return
    expect(formatTime(date)).toBe('01-02')
  })
})
