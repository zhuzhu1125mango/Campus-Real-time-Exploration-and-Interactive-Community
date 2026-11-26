import { test, expect } from '@playwright/test'
import { mockApi } from './support/api-mock'

test('首页渲染并可通过导航进入论坛', async ({ page }) => {
  await mockApi(page)

  await page.goto('/')

  await expect(page.locator('.hero-title')).toContainText('校园实时互动社区')
  await expect(page.locator('.nav-links').getByRole('link', { name: '论坛' })).toBeVisible()

  await page.locator('.nav-links').getByRole('link', { name: '论坛' }).click()

  await expect(page).toHaveURL(/\/forum$/)
  await expect(page.getByRole('heading', { name: '校园论坛' })).toBeVisible()
})

test('桌面导航展示主要入口', async ({ page }) => {
  await mockApi(page)
  await page.goto('/')

  for (const label of ['首页', '探索', '院校', '论坛', '学习']) {
    await expect(page.locator('.nav-links').getByRole('link', { name: label, exact: true })).toBeVisible()
  }
})
