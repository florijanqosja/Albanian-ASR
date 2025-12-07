import createMiddleware from "next-intl/middleware";
import {defaultLocale, localePrefix, locales} from "./i18n/routing";

export default createMiddleware({
  locales,
  defaultLocale,
  localePrefix,
  // Keep English as the default unless a locale is explicitly chosen.
  localeDetection: false,
});

export const config = {
  matcher: ["/((?!api|_next|.*\\..*).*)"],
};
