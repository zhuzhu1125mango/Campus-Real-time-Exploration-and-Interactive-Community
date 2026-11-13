#!/usr/bin/env node
/**
 * 微信小程序基础冒烟检查
 *
 * 不依赖微信开发者工具，仅做静态校验：
 * 1. manifest.json / pages.json JSON 格式合法
 * 2. pages.json 中声明的页面文件存在
 * 3. main.js 及 api/、utils/ 下 JS 文件语法可解析
 *
 * 用法：
 *   cd mp-weixin
 *   node scripts/smoke_check.js
 */

const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')

const ROOT = path.resolve(__dirname, '..')
let hasError = false

function error(message) {
  hasError = true
  console.error(`[FAIL] ${message}`)
}

function ok(message) {
  console.log(`[OK] ${message}`)
}

function readJson(filePath) {
  const full = path.join(ROOT, filePath)
  if (!fs.existsSync(full)) {
    error(`找不到文件: ${filePath}`)
    return null
  }
  try {
    const data = JSON.parse(fs.readFileSync(full, 'utf8'))
    ok(`${filePath} JSON 格式合法`)
    return data
  } catch (e) {
    error(`${filePath} JSON 解析失败: ${e.message}`)
    return null
  }
}

function checkPageExists(pagePath) {
  const vueFile = path.join(ROOT, `${pagePath}.vue`)
  if (!fs.existsSync(vueFile)) {
    error(`页面文件缺失: ${pagePath}.vue`)
    return false
  }
  return true
}

function checkJsSyntax(filePath) {
  const full = path.join(ROOT, filePath)
  try {
    execFileSync(process.execPath, ['--check', full], { stdio: 'pipe' })
    ok(`JS 语法检查通过: ${filePath}`)
    return true
  } catch (e) {
    error(`JS 语法检查失败: ${filePath}\n${e.stderr || e.message}`)
    return false
  }
}

function walkJsFiles(dir) {
  const fullDir = path.join(ROOT, dir)
  if (!fs.existsSync(fullDir)) return []
  return fs
    .readdirSync(fullDir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.js'))
    .map((entry) => path.join(dir, entry.name))
}

function main() {
  console.log('=== 微信小程序基础冒烟检查 ===\n')

  // 1. 校验 JSON 配置文件
  const manifest = readJson('manifest.json')
  const pagesConfig = readJson('pages.json')

  // 2. 检查页面文件存在性
  const declaredPages = new Set()
  if (pagesConfig && Array.isArray(pagesConfig.pages)) {
    let existsCount = 0
    for (const page of pagesConfig.pages) {
      if (page && page.path) {
        declaredPages.add(page.path)
        if (checkPageExists(page.path)) {
          existsCount++
        }
      }
    }
    ok(`pages.json 声明的 ${existsCount}/${pagesConfig.pages.length} 个页面文件已找到`)
  }

  // 3. 检查 tabBar 配置合法性
  if (pagesConfig && pagesConfig.tabBar && Array.isArray(pagesConfig.tabBar.list)) {
    let tabBarOk = true
    for (const item of pagesConfig.tabBar.list) {
      if (!item.pagePath) {
        error('tabBar 项缺少 pagePath')
        tabBarOk = false
        continue
      }
      if (!declaredPages.has(item.pagePath)) {
        error(`tabBar pagePath 未在 pages 中声明: ${item.pagePath}`)
        tabBarOk = false
      }
      if (!checkPageExists(item.pagePath)) {
        tabBarOk = false
      }
    }
    if (tabBarOk) {
      ok(`tabBar ${pagesConfig.tabBar.list.length} 个入口页面均合法`)
    }
  }

  // 4. 检查 manifest.json 关键字段
  if (manifest) {
    const requiredFields = ['name', 'appid', 'versionName', 'versionCode']
    for (const field of requiredFields) {
      if (!manifest[field]) {
        error(`manifest.json 缺少关键字段: ${field}`)
      }
    }
    if (manifest.vueVersion !== '3') {
      error(`manifest.vueVersion 应为 "3"，当前: ${manifest.vueVersion}`)
    }
    if (requiredFields.every((f) => manifest[f]) && manifest.vueVersion === '3') {
      ok('manifest.json 关键字段完整')
    }
  }

  // 5. 检查 JS 语法
  const jsFiles = ['main.js', ...walkJsFiles('api'), ...walkJsFiles('utils')]
  for (const file of jsFiles) {
    checkJsSyntax(file)
  }

  console.log('\n=== 检查结束 ===')
  if (hasError) {
    console.error('存在失败项，请修复后重试。')
    process.exit(1)
  }
  console.log('所有基础冒烟检查通过。')
}

main()
