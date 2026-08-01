export const FPS = 30;

export const timeline = {
  unsent: {from: 0, duration: 120},
  landing: {from: 120, duration: 150},
  picker: {from: 270, duration: 180},
  scenarioForm: {from: 450, duration: 240},
  personSetup: {from: 690, duration: 210},
  persona: {from: 900, duration: 240},
  conversation: {from: 1140, duration: 300},
  mechanism: {from: 1440, duration: 240},
  dynamics: {from: 1680, duration: 210},
  report: {from: 1890, duration: 270},
  rewrite: {from: 2160, duration: 150},
  outro: {from: 2310, duration: 90},
} as const;

export const PRODUCT_FILM_DURATION = 2400;
