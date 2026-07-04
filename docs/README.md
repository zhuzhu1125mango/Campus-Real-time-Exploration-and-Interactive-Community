# 校园实时探索与互动社区 - 文档中心

欢迎来到项目文档中心，这里集中存放了项目的所有文档资料。

## 文档目录

### 快速导航

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主说明 |
| [部署指南](deployment.md) | 项目部署说明 |
| [API文档/api/](api/) | API接口文档 |
| [需求规格/specs/](specs/) | 产品需求文档 |
| [功能规划/plans/](plans/) | 功能扩展计划 |
| [测试报告/tests/](tests/) | 测试报告 |
| [开发指南/guides/](guides/) | 开发规范指南 |

### 1. API文档

- [后端API文档](api/backend_api.md) - 后端API接口说明
- [前端API调用文档](api/frontend_api.md) - 前端API调用示例

### 2. 需求规格

- [产品需求文档](specs/prd.md) - PRD产品需求文档
- [检查清单](specs/checklist.md) - 开发检查清单
- [任务清单](specs/tasks.md) - 任务追踪清单

### 3. 功能规划

- [论坛功能扩展计划](plans/forum_expansion.md) - 论坛功能扩展规划

### 4. 测试报告

- [测试报告](tests/test_report.md) - 完整测试报告

### 5. 开发指南

- [开发行为指南](guides/claude.md) - 开发规范和最佳实践

## 项目概述

本项目是一个校园实时互动社区平台，旨在为用户提供校园信息查询、论坛互动、活动管理等功能。项目采用前后端分离架构：

- **后端**: Django 6.0.2 + Django REST Framework
- **前端**: Vue 3 + TypeScript + Element Plus
- **实时通信**: WebSocket (Django Channels)
- **数据库**: MySQL 8.0 / SQLite

## 核心功能

1. **院校查询和评价** - 浏览学校列表、查看详情、专业查询、分数线查询
2. **智能推荐系统** - 基于用户行为的个性化推荐
3. **校园论坛** - 帖子发布、评论回复、点赞收藏
4. **用户系统** - 用户注册登录、个人资料管理、好友系统
5. **校园活动管理** - 活动列表、报名管理
6. **实时聊天** - WebSocket实时通信
7. **数据可视化仪表盘** - 统计数据展示

## 快速开始

### 开发环境

```bash
# 后端启动
cd djangoend
python start_server.py

# 前端启动
cd frontvue
npm run dev
```

### 部署说明

详细部署步骤请参考 [部署指南](deployment.md)

## 联系方式

如有问题或建议，请通过 Issue 联系我们。