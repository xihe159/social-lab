/**
 * Social Lab 视频设计系统
 *
 * 这些 Token 来自 V2 策划稿对原项目 UI 的总结。
 * 场景组件应优先引用这里的值，不要重复散落色值、阴影和字体栈。
 */

export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
  safeArea: 72,
} as const;

export const COLORS = {
 // 页面与表面
  page: "#F4F6FB",
  pageSoft: "#F8F9FD",
  surface: "#FFFFFF",

  // 文字
  textPrimary: "#23243A",
  textSecondary: "#6F7190",
  textMuted: "#9A9BB2",

  // 结构
  border: "#E7E8F2",
  borderStrong: "#D9DBE9",

  // 品牌
  brand: "#2F2F63",
  brandPressed: "#25254F",

  // 薰衣草
  lavender: "#ECEBFD",
  lavenderSurface: "#F0EDFF",

  // 青柠
  lime: "#C8F47A",
  limeSoft: "#ECFFD2",
  limeText: "#2D4630",

  // CTA
  cta: "#4F9D7A",
  ctaHover: "#438A6B",

  // 提醒
  riskSoft: "#F8ECE8",
  warningSoft: "#FFF6DF",

  // 场景选择模态框
  modalYellow: "#FFF05B",
  modalDark: "#15182B",

  // 首页 Preview 概率条
  previewBlue: "#4563F4",
  previewAmber: "#F0B84F",
  previewRed: "#DE6B64",
  previewSlate: "#8FA0B8",
} as const;

export const TYPOGRAPHY = {
  fontFamily:
    'Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif',

  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extraBold: 800,
  },

  size: {
    label: 18,
    body: 22,
    bodyLarge: 26,
    cardTitle: 30,
    pageTitle: 52,
    sceneCopy: 42,
    hero: 84,
    brand: 96,
  },

  lineHeight: {
    compact: 1.15,
    normal: 1.45,
    relaxed: 1.65,
  },
} as const;

export const RADII = {
  input: 12,
  card: 16,
  hero: 22,
  logo: 16,
  pill: 999,
} as const;

export const SHADOWS = {
  card: "0 14px 36px rgba(43, 45, 90, 0.08)",
  floating: "0 24px 60px rgba(43, 45, 90, 0.12)",
  button: "0 12px 28px rgba(79, 157, 122, 0.24)",
  focus: "0 0 0 4px rgba(47, 47, 99, 0.08)",
} as const;

export const SPACING = {
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  section: 72,
} as const;

export const LAYOUT = {
  sidebarWidth: 296,
  contentWidth: 860,
  formWidth: 760,
  browserChromeHeight: 48,

  landingContentWidth: 1320,
  landingHeroHeight: 520,
} as const;

/**
 * 常用 Remotion 动效参数。
 * 保持高阻尼、低回弹，符合 Social Lab 克制温和的 UI 气质。
 */
export const MOTION = {
  gentleSpring: {
    damping: 200,
    stiffness: 120,
    mass: 0.7,
  },

  cardSpring: {
    damping: 180,
    stiffness: 140,
    mass: 0.8,
  },

  pressScale: 0.988,
  smallLift: 18,
  mediumLift: 24,
} as const;


