<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/* 全局 CSS 变量，与 H5 设计令牌对齐 */
	page {
		--primary-50: #eef1ff;
		--primary-100: #d9e0ff;
		--primary-200: #bbc5ff;
		--primary-300: #8e9fff;
		--primary-400: #5a6dfb;
		--primary-500: #4361ee;
		--primary-600: #2c43d5;
		--primary-700: #2434ad;
		--primary-800: #222e8d;
		--primary-900: #212b6f;

		--success-color: #10b981;
		--warning-color: #f59e0b;
		--error-color: #ef4444;
		--info-color: #3b82f6;

		--text-primary: #1f2937;
		--text-secondary: #6b7280;
		--text-tertiary: #9ca3af;
		--text-inverse: #ffffff;
		--text-link: var(--primary-500);

		--bg-primary: #ffffff;
		--bg-secondary: #f9fafc;
		--bg-tertiary: #f3f4f6;

		--border-color: #e5e7eb;
		--border-color-light: #f3f4f6;

		--space-1: 5rpx;
		--space-2: 10rpx;
		--space-3: 15rpx;
		--space-4: 20rpx;
		--space-5: 25rpx;
		--space-6: 30rpx;
		--space-8: 40rpx;
		--space-10: 50rpx;
		--space-12: 60rpx;

		--radius-sm: 4rpx;
		--radius-md: 8rpx;
		--radius-lg: 12rpx;
		--radius-xl: 16rpx;
		--radius-full: 9999rpx;

		--safe-area-bottom: env(safe-area-inset-bottom);

		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		font-size: 14px;
		line-height: 1.6;
		color: var(--text-primary);
		background-color: var(--bg-secondary);
	}

	page,
	view,
	text,
	input,
	button,
	textarea {
		box-sizing: border-box;
	}

	image {
		max-width: 100%;
		display: block;
	}

	/* 安全区占位类 */
	.safe-area-bottom {
		padding-bottom: var(--safe-area-bottom);
	}
</style>
