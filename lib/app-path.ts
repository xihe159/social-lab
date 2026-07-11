const BASE_PATH = "/social-lab";

export function appPath(path = "/") {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized === "/") return `${BASE_PATH}/`;
  return `${BASE_PATH}${normalized.endsWith("/") ? normalized : `${normalized}/`}`;
}
