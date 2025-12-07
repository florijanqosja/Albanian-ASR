import {getRequestConfig} from "next-intl/server";
import {notFound} from "next/navigation";
import {defaultLocale, locales} from "./routing";

type Locale = (typeof locales)[number];

export default getRequestConfig(async ({locale}) => {
  const normalizedLocale = (() => {
    if (!locale) return defaultLocale as Locale;
    const base = locale.split("-")[0] as Locale;
    return locales.includes(base) ? base : defaultLocale;
  })();

  if (!locales.includes(normalizedLocale)) {
    notFound();
  }

  const messages = (await import(`../messages/${normalizedLocale}.json`)).default;

  return {
    locale: normalizedLocale,
    messages,
  };
});
