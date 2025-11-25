import type { Metadata } from "next";
import { Khula } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import InitColorSchemeScript from "@mui/material/InitColorSchemeScript";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import StyledComponentsRegistry from "../lib/registry";
import theme from "../src/theme";
import "./globals.css";

const khula = Khula({
  weight: ["300", "400", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-khula",
});

export const metadata: Metadata = {
  title: "DibraSpeaks",
  description: "Albanian Speech-to-Text AI Tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${khula.variable} antialiased`}
      >
        <InitColorSchemeScript attribute="class" />
        <AppRouterCacheProvider
          options={{
            enableCssLayer: true,
          }}
        >
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <StyledComponentsRegistry>{children}</StyledComponentsRegistry>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
