import type { NextConfig } from "next";
import path from "path";
import dotenv from "dotenv";

// Load environment variables from the parent directory
dotenv.config({ path: path.resolve(__dirname, "../.env") });

const nextConfig: NextConfig = {
  /* config options here */
  outputFileTracingRoot: path.join(__dirname, "./"),
  
  // Enable standalone output for production Docker builds
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,
};

export default nextConfig;
