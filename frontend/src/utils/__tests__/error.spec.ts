import { describe, expect, it } from 'vitest'

import { getApiErrorMessage, getErrorMessage } from '../error'

describe('error utils', () => {
  describe('getErrorMessage', () => {
    it('extracts message from Error instance', () => {
      expect(getErrorMessage(new Error('boom'))).toBe('boom')
    })

    it('extracts message from plain object', () => {
      expect(getErrorMessage({ message: '对象错误' })).toBe('对象错误')
    })

    it('falls back to default message', () => {
      expect(getErrorMessage(null)).toBe('未知错误')
      expect(getErrorMessage(undefined, '默认提示')).toBe('默认提示')
    })
  })

  describe('getApiErrorMessage', () => {
    it('prefers detail from response data', () => {
      expect(
        getApiErrorMessage({ response: { data: { detail: '未认证' } } })
      ).toBe('未认证')
    })

    it('supports error, message and non_field_errors', () => {
      expect(getApiErrorMessage({ response: { data: { error: '参数错误' } } })).toBe('参数错误')
      expect(getApiErrorMessage({ response: { data: { message: '失败' } } })).toBe('失败')
      expect(
        getApiErrorMessage({ response: { data: { non_field_errors: ['重复提交'] } } })
      ).toBe('重复提交')
    })

    it('falls back to Error message or default', () => {
      expect(getApiErrorMessage(new Error('网络错误'))).toBe('网络错误')
      expect(getApiErrorMessage({}, '请求失败')).toBe('请求失败')
    })
  })
})
