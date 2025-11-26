import type { NextConfig } from "next";
import path from "path";
import dotenv from "dotenv";

// Load environment variables from the parent directory
dotenv.config({ path: path.resolve(__dirname, "../.env") });

const nextConfig: NextConfig = {
  /* config options here */
  outputFileTracingRoot: path.join(__dirname, "./"),
};

export default nextConfig;
