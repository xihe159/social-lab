import {staticFile} from "remotion";

export const SOUNDS = {
  click: {
    primary01: staticFile(
      "audio/sfx/click/mouse-click.mp3",
    ),
    primary02: staticFile(
      "audio/sfx/click/mouse-click-close.wav",
    ),
    secondary01: staticFile(
      "audio/sfx/click/classic-click.wav",
    ),
  },

  typing: {
    key01: staticFile(
      "audio/sfx/typing/slow-typing-on-a-keyboard.wav",
    ),
    key02: staticFile(
      "audio/sfx/typing/typing-on-a-laptop-keyboard.wav",
    ),
    loop: staticFile(
      "audio/sfx/typing/typing-sound.mp3",
    ),
  },

  // 使用复数名称，避免被 Remotion ESLint 误判为 CSS transition。
  transitions: {
    modalOpen: staticFile(
      "audio/sfx/transition/washing-machine-open.wav",
    ),
    pageSoft: staticFile(
      "audio/sfx/transition/flipcard.mp3",
    ),
    cardSlide: staticFile(
      "audio/sfx/transition/card-sounds.mp3",
    ),
  },

  status: {
    selected: staticFile(
      "audio/sfx/status/menu-selection.mp3",
    ),
    completed: staticFile(
      "audio/sfx/status/simple-notify-completed-process.mp3",
    ),
    reportReady: staticFile(
      "audio/sfx/status/report-ready.wav",
    ),
    agentPulse: staticFile(
      "audio/sfx/status/smooth-completed-notify-starting-alert.mp3",
    ),
  },

  brand: {
    logo: staticFile(
      "audio/sfx/brand/elegant-logo-reveal.mp3",
    ),
  },
} as const;

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
  const index = safeSeed % values.length;

  return values[index];
};
