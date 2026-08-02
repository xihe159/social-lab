import {staticFile} from "remotion";

/**
 * 语义化音效资源表。
 *
 * 所有相对路径都以 video/public 为根目录。
 * 后期只需替换这里的文件名，或通过 ProductAudioTrack 的
 * settings.assetOverrides 在运行时覆盖，不需要改时间轴代码。
 */
export const SOUND_ASSET_FILES = {
  "click.primary": "click/mouse-click.mp3",
  "click.alternate": "click/mouse-click-close.wav",
  "click.secondary": "click/classic-click.wav",
  "click.soft": "click/soft-click.mp3",
  "click.quick": "click/quick-click.mp3",

  "typing.keySlow": "typing/slow-typing-on-a-keyboard.wav",
  "typing.keyLaptop": "typing/typing-on-a-laptop-keyboard.wav",
  "typing.loop": "typing/typing-sound.mp3",

  "transition.modalOpen": "transition/washing-machine-open.wav",
  "transition.pageSoft": "transition/flipcard.mp3",
  "transition.cardSlide": "transition/card-sounds.mp3",

  "status.selected": "status/menu-selection.mp3",
  "status.completed": "status/simple-notify-completed-process.mp3",
  "status.reportReady": "status/clicking-interface-select.mp3",
  "status.agentPulse":
    "status/smooth-completed-notify-starting-alert.mp3",

  "brand.logo": "brand/elegant-logo-reveal.mp3",
} as const;

export type SoundAssetId = keyof typeof SOUND_ASSET_FILES;
export type SoundAssetOverrides = Partial<Record<SoundAssetId, string>>;

const ABSOLUTE_OR_REMOTE_SOURCE = /^(?:https?:|data:|blob:|\/)/i;

/**
 * 将 public 相对路径、站内绝对路径或远程 URL 统一转换成 Audio 可用的 src。
 */
export const resolveSoundSource = (
  assetId: SoundAssetId,
  overrides: SoundAssetOverrides = {},
): string => {
  const source = overrides[assetId] ?? SOUND_ASSET_FILES[assetId];

  if (ABSOLUTE_OR_REMOTE_SOURCE.test(source)) {
    return source;
  }

  return staticFile(source.replace(/^\.\//, ""));
};

export const selectDeterministicValue = <T>(
  values: readonly T[],
  seed: number,
): T => {
  if (values.length === 0) {
    throw new Error(
      "selectDeterministicValue requires at least one value",
    );
  }

  const safeSeed = Math.abs(Math.trunc(seed));
  return values[safeSeed % values.length];
};
