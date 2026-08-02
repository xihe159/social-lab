import type {SoundAssetOverrides} from "./sound-library";

export type AudioCategory =
  | "click"
  | "typing"
  | "transition"
  | "status"
  | "brand";

export type StudioAudioMode = "off" | "key" | "full";

export type AudioCategoryVolumes = Record<AudioCategory, number>;

export type ProductAudioSettings = Readonly<{
  enabled: boolean;
  masterVolume: number;
  categoryVolumes: AudioCategoryVolumes;
  studioMode: StudioAudioMode;
  /**
   * 是否在 Remotion Studio 时间轴中显示每个音效片段。
   * Scene 级音轨分组始终保留，避免某一 Scene 在时间轴中消失。
   */
  showInTimeline: boolean;
  /**
   * 音效正式播放前提前挂载的帧数，用于避免场景首帧音效因缓冲而漏播。
   */
  premountFrames: number;
  mutedCueIds: readonly string[];
  assetOverrides: SoundAssetOverrides;
}>;

export type ProductAudioSettingsInput = Readonly<
  Partial<
    Omit<
      ProductAudioSettings,
      "categoryVolumes" | "mutedCueIds" | "assetOverrides"
    >
  > & {
    categoryVolumes?: Partial<AudioCategoryVolumes>;
    mutedCueIds?: readonly string[];
    assetOverrides?: SoundAssetOverrides;
  }
>;

export const DEFAULT_PRODUCT_AUDIO_SETTINGS: ProductAudioSettings = {
  enabled: true,
  masterVolume: 1,
  categoryVolumes: {
    click: 1,
    typing: 0.82,
    transition: 0.9,
    status: 0.95,
    brand: 0.9,
  },
  studioMode: "full",
  // Remotion 的 Audio 默认会显示在时间轴中。这里保持 true，
  // 防止 Scene 02 等仅包含短音效的场景看起来像整段音轨消失。
  showInTimeline: true,
  // 30fps 下提前 12 帧（0.4 秒）挂载，足够让场景首帧短音效完成缓冲。
  premountFrames: 12,
  mutedCueIds: [],
  assetOverrides: {},
};

const clampVolume = (value: number): number => {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.min(1, Math.max(0, value));
};

const clampFrameCount = (value: number): number => {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.floor(value));
};

export const resolveProductAudioSettings = (
  input: ProductAudioSettingsInput = {},
): ProductAudioSettings => {
  return {
    enabled: input.enabled ?? DEFAULT_PRODUCT_AUDIO_SETTINGS.enabled,
    masterVolume: clampVolume(
      input.masterVolume ?? DEFAULT_PRODUCT_AUDIO_SETTINGS.masterVolume,
    ),
    categoryVolumes: {
      click: clampVolume(
        input.categoryVolumes?.click ??
          DEFAULT_PRODUCT_AUDIO_SETTINGS.categoryVolumes.click,
      ),
      typing: clampVolume(
        input.categoryVolumes?.typing ??
          DEFAULT_PRODUCT_AUDIO_SETTINGS.categoryVolumes.typing,
      ),
      transition: clampVolume(
        input.categoryVolumes?.transition ??
          DEFAULT_PRODUCT_AUDIO_SETTINGS.categoryVolumes.transition,
      ),
      status: clampVolume(
        input.categoryVolumes?.status ??
          DEFAULT_PRODUCT_AUDIO_SETTINGS.categoryVolumes.status,
      ),
      brand: clampVolume(
        input.categoryVolumes?.brand ??
          DEFAULT_PRODUCT_AUDIO_SETTINGS.categoryVolumes.brand,
      ),
    },
    studioMode:
      input.studioMode ?? DEFAULT_PRODUCT_AUDIO_SETTINGS.studioMode,
    showInTimeline:
      input.showInTimeline ??
      DEFAULT_PRODUCT_AUDIO_SETTINGS.showInTimeline,
    premountFrames: clampFrameCount(
      input.premountFrames ??
        DEFAULT_PRODUCT_AUDIO_SETTINGS.premountFrames,
    ),
    mutedCueIds: input.mutedCueIds ?? [],
    assetOverrides: input.assetOverrides ?? {},
  };
};
