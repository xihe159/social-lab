import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  basePath: "/social-lab",
  assetPrefix: "/social-lab/",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
