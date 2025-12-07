import {createNavigation} from "next-intl/navigation";

export const locales = ["en", "sq"] as const;
export const defaultLocale = "en" as const;
export const localePrefix = "as-needed" as const;

export const pathnames = {
  "/": "/",
  "/validate": "/validate",
  "/record": "/record",
  "/login": "/login",
  "/register": "/register",
  "/forgot-password": "/forgot-password",
  "/reset-password": "/reset-password",
  "/verify": "/verify",
  "/profile": "/profile",
  "/my-labels": "/my-labels",
  "/termsandservices": "/termsandservices",
} as const;

export const {Link, redirect, usePathname, useRouter, permanentRedirect} =
  createNavigation({
    locales,
    defaultLocale,
    localePrefix,
    pathnames,
  });
