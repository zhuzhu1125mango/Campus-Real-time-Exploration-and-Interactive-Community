import { test, expect } from '@playwright/test'
import { mockApi } from './support/api-mock'

test('论坛展示最新主题并可进入主题详情', async ({ page }) => {
  await mockApi(page)

  await page.goto('/forum')

  await expect(page.getByRole('heading', { name: '校园论坛' })).toBeVisible()
  const topicItem = page.locator('.latest-topic-item', { hasText: 'E2E 测试主题' })
  await expect(topicItem).toBeVisible()

  await topicItem.click()

  await expect(page).toHaveURL(/\/forum\/topic\/1$/)
  await expect(page.getByRole('heading', { name: 'E2E 测试主题' })).toBeVisible()
  await expect(page.getByText('这是首帖内容')).toBeVisible()
})
