import config from './config'

export function buildMediaUrl(url: string | null | undefined, defaultUrl: string): string {
  if (!url) {
    return `${config.media.baseUrl}${defaultUrl}`
  }

  if (url.startsWith('http') || url.startsWith('data:')) {
    return url
  }

  const baseUrl = config.media.baseUrl
  if (url.startsWith('/')) {
    return `${baseUrl}${url}`
  } else {
    return `${baseUrl}/${url}`
  }
}

export function isValidUrl(url: string): boolean {
  return url.startsWith('http') || url.startsWith('data:') || url.startsWith('/')
}

export function getFullApiUrl(path: string): string {
  if (path.startsWith('http')) {
    return path
  }
  
  const baseUrl = config.apiBaseUrl
  if (path.startsWith('/')) {
    return `${baseUrl}${path}`
  } else {
    return `${baseUrl}/${path}`
  }
}