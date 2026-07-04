

interface TokenExpiryOptions {
  onExpiry?: () => void
  onExpiringSoon?: () => void
  checkInterval?: number
  warningThreshold?: number
}

export class TokenExpiryService {
  private checkInterval: number | null = null
  private options: Required<TokenExpiryOptions>

  constructor(options: TokenExpiryOptions = {}) {
    this.options = {
      onExpiry: options.onExpiry || (() => {}),
      onExpiringSoon: options.onExpiringSoon || (() => {}),
      checkInterval: options.checkInterval || 5 * 60 * 1000,
      warningThreshold: options.warningThreshold || 60 * 60 * 1000
    }
  }

  setTokenExpiry(expiresIn: number): void {
    const now = Date.now()
    const expiryTime = now + expiresIn
    localStorage.setItem('token_expiry', expiryTime.toString())
    localStorage.setItem('login_time', now.toString())
  }

  checkExpiry(): boolean {
    const expiryTimeStr = localStorage.getItem('token_expiry')
    if (!expiryTimeStr) return true

    const expiryTime = parseInt(expiryTimeStr)
    const now = Date.now()

    if (now > expiryTime) {
      this.options.onExpiry()
      return true
    }

    const timeUntilExpiry = expiryTime - now
    if (timeUntilExpiry <= this.options.warningThreshold) {
      this.options.onExpiringSoon()
    }

    return false
  }

  startExpiryCheck(): void {
    if (this.checkInterval) {
      this.stopExpiryCheck()
    }

    this.checkExpiry()

    this.checkInterval = window.setInterval(() => {
      this.checkExpiry()
    }, this.options.checkInterval)
  }

  stopExpiryCheck(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
      this.checkInterval = null
    }
  }

  clearExpiry(): void {
    this.stopExpiryCheck()
    localStorage.removeItem('token_expiry')
    localStorage.removeItem('login_time')
    localStorage.removeItem('token_check_interval')
  }

  getRemainingTime(): number | null {
    const expiryTimeStr = localStorage.getItem('token_expiry')
    if (!expiryTimeStr) return null

    const expiryTime = parseInt(expiryTimeStr)
    const now = Date.now()

    return expiryTime - now
  }
}

const TOKEN_EXPIRY_DAYS = 7

export function createDefaultExpiryService(onExpiry: () => void): TokenExpiryService {
  return new TokenExpiryService({
    onExpiry,
    onExpiringSoon: () => {
      if (typeof window !== 'undefined') {
        const confirmRefresh = confirm('您的登录会话将在1小时内过期，是否重新登录以延长会话？')
        if (confirmRefresh) {
          window.location.href = '/login'
        }
      }
    },
    checkInterval: 5 * 60 * 1000,
    warningThreshold: 60 * 60 * 1000
  })
}

export function getTokenExpiryDays(): number {
  return TOKEN_EXPIRY_DAYS
}

export function calculateExpiryTime(): number {
  return TOKEN_EXPIRY_DAYS * 24 * 60 * 60 * 1000
}