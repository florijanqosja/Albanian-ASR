import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import InitColorSchemeScript from "@mui/material/InitColorSchemeScript";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import StyledComponentsRegistry from "../../lib/registry";
import AuthContext from "../../src/context/AuthContext";
import ProfileCompletionWrapper from "../../src/context/ProfileCompletionWrapper";
import theme from "../../src/theme";
import TopNavbar from "../../src/components/Nav/TopNavbar";
import "../globals.css";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
});

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Omit<Props, "children">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });

  return {
    title: t("title"),
    description: t("description"),
    icons: {
      icon: "/favicon.ico",
      shortcut: "/favicon.ico",
      apple: "/favicon.ico",
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: Props) {
  const { locale } = await params;
  const messages = await getMessages({ locale });

  return (
    <html lang={locale} suppressHydrationWarning>
      <body
        className={`${inter.variable} antialiased bg-gray-50`}
      >
        <InitColorSchemeScript attribute="class" />
        <AppRouterCacheProvider
          options={{
            enableCssLayer: true,
          }}
        >
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <NextIntlClientProvider locale={locale} messages={messages}>
              <AuthContext>
                <ProfileCompletionWrapper>
                  <StyledComponentsRegistry>
                    <TopNavbar />
                    <main className="min-h-screen pt-4">
                      {children}
                    </main>
                  </StyledComponentsRegistry>
                </ProfileCompletionWrapper>
              </AuthContext>
            </NextIntlClientProvider>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
