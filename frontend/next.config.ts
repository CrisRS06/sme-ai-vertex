import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Para Firebase Hosting (static export)
  images: {
    unoptimized: true,  // Necesario para static export
  },
  // Configuración de trailing slash para Firebase
  trailingSlash: true,
};

export default nextConfig;
