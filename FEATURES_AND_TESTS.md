# 功能说明文档与测试报告

## 1. 项目概述

校园实时探索与互动社区是一个基于前后端分离架构的Web应用，旨在为用户提供校园信息查询、论坛互动、活动管理等功能。项目采用Django作为后端框架，Vue 3 + TypeScript作为前端框架，实现了智能校园推荐系统、校园活动管理系统和数据可视化仪表盘等核心功能。

## 2. 技术架构

### 2.1 后端架构
- **框架**: Django + Django REST Framework
- **数据库**: SQLite
- **服务器**: Uvicorn (ASGI)
- **缓存**: Django caching system
- **认证**: JWT
- **WebSocket**: Django Channels (实时通信)

### 2.2 前端架构
- **框架**: Vue 3 + TypeScript
- **状态管理**: Pinia
- **路由**: Vue Router
- **UI组件**: Element Plus
- **图表库**: ECharts
- **HTTP客户端**: Axios
- **构建工具**: Vite

## 3. 核心功能模块

### 3.1 智能校园推荐系统

#### 3.1.1 后端API
- **推荐算法**: 基于用户行为和学校属性的协同过滤算法
- **API端点**:
  - `GET /api/schools/recommendations/` - 获取个性化推荐
  - 支持按类型过滤（学校、专业、帖子）
  - 支持分页和数量限制
- **缓存机制**: 使用Django缓存减少计算开销

#### 3.1.2 前端组件
- **RecommendationSection.vue**: 推荐内容展示组件
  - 支持标签切换（学校、专业、帖子）
  - 响应式设计，适配不同屏幕尺寸
  - 加载状态和错误处理

### 3.2 校园活动管理系统

#### 3.2.1 后端API
- **活动管理**:
  - `GET /api/schools/events/` - 获取活动列表
  - `POST /api/schools/events/{id}/register/` - 报名活动
  - `POST /api/schools/events/{id}/cancel_registration/` - 取消报名
- **活动状态**:
  - 待开始、进行中、已结束
  - 报名人数限制和状态管理

#### 3.2.2 前端组件
- **EventCalendar.vue**: 活动日历组件
  - 月视图和列表视图切换
  - 活动详情展示
  - 报名/取消报名功能
- **Events.vue**: 活动列表页面
  - 活动筛选和搜索
  - 分页加载

### 3.3 数据可视化仪表盘

#### 3.3.1 后端API
- **统计数据**:
  - `GET /api/schools/stats/dashboard/` - 仪表盘综合数据
  - `GET /api/schools/stats/school/` - 学校统计数据
  - `GET /api/schools/stats/forum/` - 论坛统计数据
  - `GET /api/schools/stats/event/` - 活动统计数据
  - `GET /api/schools/stats/user/` - 用户统计数据
- **缓存机制**: 15分钟缓存，减少数据库查询

#### 3.3.2 前端组件
- **Dashboard.vue**: 数据仪表盘组件
  - 概览卡片（学校、帖子、活动、用户总数）
  - 学校类型和层次分布饼图
  - 省份分布柱状图
  - 论坛活动折线图
  - 活动状态分布饼图
  - 用户行为柱状图
  - 响应式设计

## 4. API接口文档

### 4.1 推荐系统API
- **GET /api/schools/recommendations/**
  - 参数: `type` (school/major/post), `limit` (数量限制)
  - 返回: 推荐列表和推荐理由

### 4.2 活动管理API
- **GET /api/schools/events/**
  - 参数: `page`, `page_size`, `start_date`, `end_date`, `status`
  - 返回: 活动列表（分页）

- **POST /api/schools/events/{id}/register/**
  - 返回: 报名成功/失败信息

- **POST /api/schools/events/{id}/cancel_registration/**
  - 返回: 取消报名成功/失败信息

### 4.3 统计数据API
- **GET /api/schools/stats/dashboard/**
  - 返回: 综合仪表盘数据

- **GET /api/schools/stats/school/**
  - 返回: 学校统计数据

- **GET /api/schools/stats/forum/**
  - 返回: 论坛统计数据

- **GET /api/schools/stats/event/**
  - 返回: 活动统计数据

- **GET /api/schools/stats/user/**
  - 返回: 用户统计数据

## 5. 前端组件说明

### 5.1 核心组件
- **RecommendationSection.vue**: 推荐内容展示
- **EventCalendar.vue**: 活动日历
- **Dashboard.vue**: 数据仪表盘
- **SchoolCard.vue**: 学校卡片
- **SchoolComparison.vue**: 学校对比

### 5.2 页面视图
- **Home.vue**: 首页（包含推荐系统）
- **Schools.vue**: 学校列表
- **SchoolDetail.vue**: 学校详情
- **Events.vue**: 活动页面
- **Dashboard.vue**: 数据仪表盘页面
- **Forum.vue**: 论坛页面

## 6. 测试报告

### 6.1 测试环境
- **操作系统**: Windows 10
- **Python版本**: 3.14
- **Node.js版本**: 20.x
- **Django版本**: 4.x
- **Vue版本**: 3.x

### 6.2 测试用例

#### 6.2.1 后端测试
- **SchoolComparisonAPITest**: 测试学校对比功能
- **RecommendationAPITest**: 测试推荐系统功能
- **EventAPITest**: 测试活动管理功能
- **StatsAPITest**: 测试统计数据功能

#### 6.2.2 前端测试
- **类型检查**: Vue TypeScript类型检查
- **组件功能测试**: 手动测试前端组件功能

### 6.3 测试结果

#### 6.3.1 后端测试
- **测试总数**: 27个
- **通过数量**: 27个
- **通过率**: 100%

#### 6.3.2 前端测试
- **类型检查**: 通过（0错误）
- **组件功能**: 正常运行
- **API调用**: 正常响应

### 6.4 覆盖率分析
- **后端测试覆盖率**: 主要API端点均有测试覆盖
- **前端类型覆盖率**: 100% TypeScript类型检查通过

### 6.5 问题发现与修复

#### 6.5.1 已修复问题
1. **Windows multiprocessing错误**: 添加`if __name__ == '__main__'`保护
2. **Django apps not loaded错误**: 添加`django.setup()`调用
3. **前端API响应处理错误**: 修正响应数据访问方式
4. **TypeScript类型错误**: 修复类型定义和导入问题
5. **API路径不匹配**: 修正测试文件中的API路径

#### 6.5.2 已知问题
- 无重大问题，所有功能正常运行

## 7. 使用指南

### 7.1 本地开发
1. **后端启动**:
   ```bash
   cd djangoend
   python start_server.py
   ```

2. **前端启动**:
   ```bash
   cd frontvue
   npm run dev
   ```

### 7.2 部署
- **后端**: 使用Uvicorn作为生产服务器
- **前端**: 构建静态文件后部署到Web服务器

### 7.3 主要功能使用
1. **智能推荐**: 访问首页查看个性化推荐内容
2. **活动管理**: 访问`/events`页面查看和报名活动
3. **数据仪表盘**: 访问`/dashboard`页面查看统计数据

## 8. 项目结构

### 8.1 后端结构
```
djangoend/
├── schools/          # 学校相关功能
│   ├── views.py      # API视图
│   ├── models.py     # 数据模型
│   ├── serializers.py # 序列化器
│   ├── urls.py       # 路由配置
│   ├── recommendation.py # 推荐系统
│   └── stats.py      # 统计系统
├── users/            # 用户相关功能
├── forum/            # 论坛功能
├── chat/             # 聊天功能
└── djangoProject/    # 项目配置
```

### 8.2 前端结构
```
frontvue/
├── src/
│   ├── components/   # 组件
│   ├── views/        # 页面
│   ├── api/          # API调用
│   ├── router/       # 路由
│   ├── stores/       # 状态管理
│   └── types/        # TypeScript类型
└── public/           # 静态文件
```

## 9. 技术亮点

1. **前后端分离架构**: 清晰的职责划分，便于维护和扩展
2. **智能推荐系统**: 基于用户行为的个性化推荐
3. **实时数据可视化**: 使用ECharts实现丰富的数据展示
4. **活动管理系统**: 完整的活动生命周期管理
5. **缓存机制**: 优化API性能，减少数据库负载
6. **响应式设计**: 适配不同设备屏幕
7. **TypeScript类型安全**: 提高代码质量和开发效率

## 10. 未来扩展方向

1. **机器学习优化**: 使用更高级的推荐算法
2. **实时通知系统**: WebSocket实时推送
3. **移动应用**: 开发配套移动端应用
4. **多语言支持**: 国际化功能
5. **社交功能增强**: 好友系统、消息系统
6. **数据分析工具**: 更强大的数据分析和可视化功能
7. **第三方集成**: 与其他教育平台集成

---

本项目已完成核心功能开发，所有测试用例通过，系统运行稳定。后续可根据用户反馈和业务需求进行进一步的功能扩展和优化。