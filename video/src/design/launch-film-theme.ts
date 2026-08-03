import {COLORS, RADII, SHADOWS, TYPOGRAPHY} from "./tokens";

export const LAUNCH_VIDEO = {
  width: 3840,
  height: 2160,
  fps: 30,
  baseWidth: 1920,
  baseHeight: 1080,
} as const;


/**
 * 横屏产品发布片专用视觉层。
 *
 * 这里不替换真实产品 Token，而是只定义“产品之外”的广告画布：
 * 背景、浮动窗口、章节标签和宣传文案。产品 UI 仍由 scenes/ 内组件渲染。
 */
export const LAUNCH_FILM = {
  background: {
    base: COLORS.page,
    soft: COLORS.pageSoft,
    dark: "#17182B",
    glowLime: "rgba(200, 244, 122, 0.38)",
    glowLavender: "rgba(236, 235, 253, 0.76)",
    grid: "rgba(47, 47, 99, 0.055)",
  },
  window: {
    border: "rgba(47, 47, 99, 0.12)",
    shadow: "0 42px 120px rgba(35, 36, 58, 0.20)",
    radius: 32,
  },
  panel: {
    width: 430,
    border: "rgba(47, 47, 99, 0.11)",
    shadow: "0 24px 72px rgba(35, 36, 58, 0.13)",
    radius: 28,
  },
  typography: {
    family: TYPOGRAPHY.fontFamily,
    eyebrow: 16,
    title: 58,
    titleLarge: 72,
    body: 22,
    metric: 82,
  },
  colors: {
    brand: COLORS.brand,
    lime: COLORS.lime,
    limeSoft: COLORS.limeSoft,
    cta: COLORS.cta,
    lavender: COLORS.lavender,
    surface: COLORS.surface,
    text: COLORS.textPrimary,
    textSecondary: COLORS.textSecondary,
    border: COLORS.border,
  },
  radii: RADII,
  shadows: SHADOWS,
} as const;
