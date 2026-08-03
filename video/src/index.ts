import {registerRoot} from "remotion";

import {RemotionRoot} from "./Root";

const preventBrowserDomTranslation = (): void => {
  if (typeof document === "undefined") {
    return;
  }

  const markAsNotranslate = (element: HTMLElement | null): void => {
    if (!element) {
      return;
    }

    element.lang = "zh-CN";
    element.setAttribute("translate", "no");
    element.classList.add("notranslate");
  };

  markAsNotranslate(document.documentElement);
  markAsNotranslate(document.body);

  if (!document.body) {
    document.addEventListener(
      "DOMContentLoaded",
      () => markAsNotranslate(document.body),
      {once: true},
    );
  }
};

preventBrowserDomTranslation();
registerRoot(RemotionRoot);
