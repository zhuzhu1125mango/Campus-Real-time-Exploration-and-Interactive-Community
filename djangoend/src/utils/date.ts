/**
 * 根据日期的新旧程度格式化日期
 * 今天的日期显示为"今天 HH:MM"
 * 昨天的日期显示为"昨天 HH:MM"
 * 一周内的日期显示为"星期X HH:MM"
 * 更早的日期显示为"YYYY-MM-DD HH:MM"
 */
export function formatDate(dateString: string): string {
  // 检查输入是否有效
  if (!dateString) {
    return '';
  }

  const date = new Date(dateString);
  
  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    return '';
  }

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  // 计算日期差异（天数）
  const diffDays = Math.floor((today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  // 格式化时间部分 HH:MM
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const timeStr = `${hours}:${minutes}`;
  
  // 今天
  if (date >= today) {
    return `今天 ${timeStr}`;
  }
  
  // 昨天
  if (date >= yesterday) {
    return `昨天 ${timeStr}`;
  }
  
  // 一周内
  if (diffDays < 7) {
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    const weekday = weekdays[date.getDay()];
    return `星期${weekday} ${timeStr}`;
  }
  
  // 更早的日期
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  
  return `${year}-${month}-${day} ${timeStr}`;
} 