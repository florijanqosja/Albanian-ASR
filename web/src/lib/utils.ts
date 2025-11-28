import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function buildFileAccessUrl(baseUrl: string | undefined, filePath: string) {
  if (!filePath) {
    return filePath
  }

  const normalizedBase = (baseUrl ?? "").replace(/\/+$/, "")
  const normalizedPath = filePath.startsWith("/") ? filePath : `/${filePath}`

  if (!normalizedBase) {
    return normalizedPath
  }

  return `${normalizedBase}${normalizedPath}`
}
