/** @type {import('next').NextConfig} */
const nextConfig = {
  images: { unoptimized: true },
  // El frontend llama al backend con rutas relativas /api/*. Next las reenvÃ­a
  // al backend local (uvicorn en :8000). AsÃ­ todo queda bajo un Ãºnico origen:
  // funciona por IP en la LAN, por localhost y detrÃ¡s de un dominio o tÃºnel
  // (ngrok / Cloudflare) sin tener que exponer el puerto 8000.
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;