import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1', withCredentials: true })

let accessToken = null

export function setToken(token) { accessToken = token }
export function getToken() { return accessToken }

api.interceptors.request.use(config => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use(
  res => res.data,
  async err => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true
      try {
        const res = await api.post('/auth/refresh')
        setToken(res.data.access_token || res.access_token)
        err.config.headers.Authorization = `Bearer ${accessToken}`
        return api(err.config)
      } catch {
        setToken(null)
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
