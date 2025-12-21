import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.redd.it",
      },
      {
        protocol: "https",
        hostname: "**.reddit.com",
      },
      {
        protocol: "https",
        hostname: "styles.redditmedia.com",
      },
      {
        protocol: "https",
        hostname: "preview.redd.it",
      },
      {
        protocol: "https",
        hostname: "i.redd.it",
      },
    ],
  },
};

export default nextConfig;



