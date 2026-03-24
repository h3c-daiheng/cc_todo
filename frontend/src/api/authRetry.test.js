import test from 'node:test'
import assert from 'node:assert/strict'
import { pathToFileURL } from 'node:url'

async function loadModule() {
  const moduleUrl = `${pathToFileURL('/root/todo/frontend/src/api/authRetry.js').href}?t=${Date.now()}-${Math.random()}`
  return import(moduleUrl)
}

test('login request 401 should not trigger refresh retry', async () => {
  const { shouldAttemptRefresh } = await loadModule()

  assert.equal(
    shouldAttemptRefresh({ status: 401, url: '/auth/login', retry: false }),
    false,
  )
})

test('refresh request 401 should not trigger nested refresh retry', async () => {
  const { shouldAttemptRefresh } = await loadModule()

  assert.equal(
    shouldAttemptRefresh({ status: 401, url: '/auth/refresh', retry: false }),
    false,
  )
})

test('protected endpoint 401 should trigger one refresh retry', async () => {
  const { shouldAttemptRefresh } = await loadModule()

  assert.equal(
    shouldAttemptRefresh({ status: 401, url: '/tasks', retry: false }),
    true,
  )
  assert.equal(
    shouldAttemptRefresh({ status: 401, url: '/tasks', retry: true }),
    false,
  )
})

test('extractErrorMessage should preserve backend detail', async () => {
  const { extractErrorMessage } = await loadModule()

  assert.equal(
    extractErrorMessage({ response: { data: { detail: '用户名或密码错误' } } }),
    '用户名或密码错误',
  )
})
