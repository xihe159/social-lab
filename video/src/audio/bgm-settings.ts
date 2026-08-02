export type ProductBgmSettings = Readonly<{
  /** 是否挂载 BGM。默认关闭，未放置文件时不会产生 404。 */
  enabled: boolean;
  /** public/ 下的相对路径，或可直接访问的 http(s) URL。 */
  src: string;
  /** 0–1。建议产品演示视频保持在 0.10–0.22。 */
  volume: number;
  /** 是否循环到视频结束。 */
  loop: boolean;
  /** 音频播放速度。1 表示原速。 */
  playbackRate: number;
  /** 跳过音频开头的帧数。 */
  trimBeforeFrames: number;
  /** 全片开头淡入帧数。 */
  fadeInFrames: number;
  /** 全片结尾淡出帧数。 */
  fadeOutFrames: number;
  /** Studio 中是否静音；正式渲染不受影响。 */
  muteInStudio: boolean;
  /** 是否在 Remotion Studio 时间轴显示 BGM。 */
  showInTimeline: boolean;
}>;

export type ProductBgmSettingsInput = Readonly<Partial<ProductBgmSettings>>;

export const DEFAULT_PRODUCT_BGM_SETTINGS: ProductBgmSettings = {
  enabled: true,
  src: "bgm/X-Ray Dog - A Laugh And A Smile.mp3",
  volume: 0.16,
  loop: true,
  playbackRate: 1,
  trimBeforeFrames: 0,
  fadeInFrames: 24,
  fadeOutFrames: 42,
  muteInStudio: false,
  showInTimeline: true,
};

const clamp = (value: number, minimum: number, maximum: number): number => {
  if (!Number.isFinite(value)) {
    return minimum;
  }

  return Math.min(maximum, Math.max(minimum, value));
};

const clampFrameCount = (value: number): number => {
  return Math.floor(clamp(value, 0, Number.MAX_SAFE_INTEGER));
};

export const resolveProductBgmSettings = (
  input: ProductBgmSettingsInput = {},
): ProductBgmSettings => {
  const src = (input.src ?? DEFAULT_PRODUCT_BGM_SETTINGS.src).trim();

  return {
    enabled: input.enabled ?? DEFAULT_PRODUCT_BGM_SETTINGS.enabled,
    src: src || DEFAULT_PRODUCT_BGM_SETTINGS.src,
    volume: clamp(
      input.volume ?? DEFAULT_PRODUCT_BGM_SETTINGS.volume,
      0,
      1,
    ),
    loop: input.loop ?? DEFAULT_PRODUCT_BGM_SETTINGS.loop,
    playbackRate: clamp(
      input.playbackRate ?? DEFAULT_PRODUCT_BGM_SETTINGS.playbackRate,
      0.0625,
      16,
    ),
    trimBeforeFrames: clampFrameCount(
      input.trimBeforeFrames ??
        DEFAULT_PRODUCT_BGM_SETTINGS.trimBeforeFrames,
    ),
    fadeInFrames: clampFrameCount(
      input.fadeInFrames ?? DEFAULT_PRODUCT_BGM_SETTINGS.fadeInFrames,
    ),
    fadeOutFrames: clampFrameCount(
      input.fadeOutFrames ?? DEFAULT_PRODUCT_BGM_SETTINGS.fadeOutFrames,
    ),
    muteInStudio:
      input.muteInStudio ?? DEFAULT_PRODUCT_BGM_SETTINGS.muteInStudio,
    showInTimeline:
      input.showInTimeline ?? DEFAULT_PRODUCT_BGM_SETTINGS.showInTimeline,
  };
};
