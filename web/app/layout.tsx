import type { Metadata } from "next";
import { Khula } from "next/font/google";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import InitColorSchemeScript from "@mui/material/InitColorSchemeScript";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import StyledComponentsRegistry from "../lib/registry";
import AuthContext from "../src/context/AuthContext";
import ProfileCompletionWrapper from "../src/context/ProfileCompletionWrapper";
import theme from "../src/theme";
import TopNavbar from "../src/components/Nav/TopNavbar";
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
        className={`${khula.variable} antialiased bg-gray-50`}
      >
        <InitColorSchemeScript attribute="class" />
        <AppRouterCacheProvider
          options={{
            enableCssLayer: true,
          }}
        >
          <ThemeProvider theme={theme}>
            <CssBaseline />
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
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
