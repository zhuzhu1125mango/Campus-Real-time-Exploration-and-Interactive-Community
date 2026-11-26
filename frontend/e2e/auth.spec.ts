import { test, expect } from '@playwright/test'
import { mockApi } from './support/api-mock'

test('未登录访问个人中心会跳转到登录页', async ({ page }) => {
  await mockApi(page)

  await page.goto('/profile')

  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: '欢迎回来' })).toBeVisible()
})

test('密码登录成功后进入首页并显示用户名', async ({ page }) => {
  await mockApi(page)
  await page.goto('/login')

  await page.locator('#username').fill('e2e_user')
  await page.locator('#password').fill('secret123')
  await page.locator('.auth-form').getByRole('button', { name: '登录', exact: true }).click()

  await expect(page).toHaveURL(/localhost:5174\/$/)
  await expect(page.locator('.hero-title')).toContainText('校园实时互动社区')
  await expect(page.locator('.nav-tools .user-name')).toHaveText('e2e_user')
})

test('密码错误时显示后端返回的错误信息', async ({ page }) => {
  await mockApi(page, { loginFails: true })
  await page.goto('/login')

  await page.locator('#username').fill('e2e_user')
  await page.locator('#password').fill('wrong-password')
  await page.locator('.auth-form').getByRole('button', { name: '登录', exact: true }).click()

  await expect(page.getByText('用户名或密码错误')).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})
