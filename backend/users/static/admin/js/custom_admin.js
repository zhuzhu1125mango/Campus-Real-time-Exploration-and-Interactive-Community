/**
 * 自定义管理后台JavaScript
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
  // 初始化所有功能
  initNavigation();
  initAnimations();
  initFormEnhancements();
  initTooltips();
});

/**
 * 初始化导航功能
 */
function initNavigation() {
  // 侧边栏导航交互
  const navLinks = document.querySelectorAll('#nav-sidebar .nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // 移除所有活动状态
      navLinks.forEach(item => item.classList.remove('active'));
      // 添加当前活动状态
      this.classList.add('active');
    });
  });

  // 响应式导航菜单
  const toggleSidebar = document.createElement('button');
  toggleSidebar.className = 'sidebar-toggle';
  toggleSidebar.innerHTML = '☰';
  toggleSidebar.style.cssText = `
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 1000;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius-md);
    padding: 0.5rem;
    cursor: pointer;
    display: none;
  `;
  document.body.appendChild(toggleSidebar);

  // 响应式处理
  function handleResponsive() {
    const sidebar = document.getElementById('content-related');
    const container = document.getElementById('container');
    
    if (window.innerWidth <= 768) {
      toggleSidebar.style.display = 'block';
      sidebar.style.transform = 'translateX(-100%)';
      sidebar.style.position = 'fixed';
      sidebar.style.top = '0';
      sidebar.style.left = '0';
      sidebar.style.height = '100vh';
      sidebar.style.zIndex = '999';
    } else {
      toggleSidebar.style.display = 'none';
      sidebar.style.transform = 'translateX(0)';
      sidebar.style.position = 'static';
      sidebar.style.height = 'auto';
    }
  }

  // 初始调用
  handleResponsive();
  
  // 窗口大小变化时调用
  window.addEventListener('resize', handleResponsive);

  // 切换侧边栏
  toggleSidebar.addEventListener('click', function() {
    const sidebar = document.getElementById('content-related');
    if (sidebar.style.transform === 'translateX(-100%)') {
      sidebar.style.transform = 'translateX(0)';
    } else {
      sidebar.style.transform = 'translateX(-100%)';
    }
  });
}

/**
 * 初始化动画效果
 */
function initAnimations() {
  // 为模块添加进入动画
  const modules = document.querySelectorAll('.module');
  modules.forEach((module, index) => {
    module.style.animationDelay = `${index * 0.1}s`;
  });

  // 为按钮添加悬停效果
  const buttons = document.querySelectorAll('.button, input[type="submit"], input[type="button"]');
  buttons.forEach(button => {
    button.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-2px)';
      this.style.boxShadow = 'var(--shadow-md)';
    });
    
    button.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = 'none';
    });
  });

  // 为表格行添加悬停效果
  const tableRows = document.querySelectorAll('table tbody tr');
  tableRows.forEach(row => {
    row.addEventListener('mouseenter', function() {
      this.style.backgroundColor = 'rgba(59, 130, 246, 0.05)';
      this.style.transition = 'background-color 0.3s ease';
    });
    
    row.addEventListener('mouseleave', function() {
      this.style.backgroundColor = '';
    });
  });
}

/**
 * 增强表单功能
 */
function initFormEnhancements() {
  // 表单输入验证
  const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea');
  formInputs.forEach(input => {
    input.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
      this.parentElement.classList.remove('focused');
      // 简单验证
      if (this.required && !this.value) {
        this.style.borderColor = 'var(--danger-color)';
      } else {
        this.style.borderColor = '';
      }
    });
  });

  // 提交按钮加载状态
  const submitButtons = document.querySelectorAll('input[type="submit"]');
  submitButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      // 防止表单重复提交
      if (this.form.checkValidity()) {
        const originalText = this.value;
        this.value = '提交中...';
        this.disabled = true;
        
        // 创建加载动画
        const loading = document.createElement('span');
        loading.className = 'loading';
        loading.style.marginLeft = '0.5rem';
        this.parentNode.appendChild(loading);
        
        // 模拟提交延迟
        setTimeout(() => {
          this.form.submit();
        }, 500);
      }
    });
  });
}

/**
 * 初始化工具提示
 */
function initTooltips() {
  // 为带data-tooltip属性的元素添加工具提示
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  tooltipElements.forEach(element => {
    element.classList.add('tooltip');
  });
}

/**
 * 显示通知消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型: success, error, warning, info
 */
function showNotification(message, type = 'info') {
  const notificationsContainer = document.querySelector('.messages') || document.body;
  
  const notification = document.createElement('div');
  notification.className = `message ${type}`;
  notification.textContent = message;
  
  // 添加到容器
  notificationsContainer.appendChild(notification);
  
  // 动画效果
  notification.style.opacity = '0';
  notification.style.transform = 'translateY(-10px)';
  notification.style.transition = 'all 0.3s ease';
  
  setTimeout(() => {
    notification.style.opacity = '1';
    notification.style.transform = 'translateY(0)';
  }, 10);
  
  // 3秒后自动消失
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(-10px)';
    
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

/**
 * 平滑滚动到指定元素
 * @param {HTMLElement} element - 目标元素
 */
function smoothScrollTo(element) {
  element.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 */
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showNotification('已复制到剪贴板', 'success');
  }).catch(err => {
    showNotification('复制失败', 'error');
    console.error('复制失败:', err);
  });
}

// 全局函数，可在模板中使用
window.showNotification = showNotification;
window.smoothScrollTo = smoothScrollTo;
window.copyToClipboard = copyToClipboard;