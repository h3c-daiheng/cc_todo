export function shouldAttemptRefresh({ status, url, retry }) {
  if (status !== 401 || retry) return false
  return url !== '/auth/login' && url !== '/auth/refresh'
}

export function extractErrorMessage(error, fallback = '登录失败') {
  return error?.response?.data?.detail || fallback
}
