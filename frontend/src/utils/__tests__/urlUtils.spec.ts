import { describe, expect, it } from 'vitest'

import config from '../config'
import { buildMediaUrl, getFullApiUrl, isValidUrl } from '../urlUtils'

describe('urlUtils', () => {
  describe('buildMediaUrl', () => {
    it('returns default url when value is empty', () => {
      expect(buildMediaUrl(null, '/media/avatars/default.svg')).toBe(
        `${config.media.baseUrl}/media/avatars/default.svg`
      )
    })

    it('keeps absolute and data urls unchanged', () => {
      expect(buildMediaUrl('https://cdn.example.com/a.png', '/default.png')).toBe(
        'https://cdn.example.com/a.png'
      )
      expect(buildMediaUrl('data:image/png;base64,abc', '/default.png')).toBe(
        'data:image/png;base64,abc'
      )
    })

    it('joins media base url with relative paths', () => {
      expect(buildMediaUrl('/media/a.png', '/default.png')).toBe(
        `${config.media.baseUrl}/media/a.png`
      )
      expect(buildMediaUrl('media/a.png', '/default.png')).toBe(
        `${config.media.baseUrl}/media/a.png`
      )
    })
  })

  describe('isValidUrl', () => {
    it('accepts http, data and absolute paths', () => {
      expect(isValidUrl('https://example.com')).toBe(true)
      expect(isValidUrl('data:image/png;base64,abc')).toBe(true)
      expect(isValidUrl('/media/a.png')).toBe(true)
    })

    it('rejects plain relative paths', () => {
      expect(isValidUrl('media/a.png')).toBe(false)
    })
  })

  describe('getFullApiUrl', () => {
    it('returns absolute urls unchanged', () => {
      expect(getFullApiUrl('https://example.com/api/users/')).toBe(
        'https://example.com/api/users/'
      )
    })

    it('prefixes paths with api base url', () => {
      expect(getFullApiUrl('/users/1/')).toBe(`${config.apiBaseUrl}/users/1/`)
      expect(getFullApiUrl('users/1/')).toBe(`${config.apiBaseUrl}/users/1/`)
    })
  })
})
