/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Configure API base URL from environment variable
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  }
};

export default nextConfig;
