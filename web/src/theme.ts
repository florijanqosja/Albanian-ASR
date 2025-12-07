"use client";
import { createTheme } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface Palette {
    accent: Palette["primary"];
    border: Palette["primary"];
  }
  interface PaletteOptions {
    accent?: PaletteOptions["primary"];
    border?: PaletteOptions["primary"];
  }
}

const theme = createTheme({
  typography: {
    fontFamily: "var(--font-inter), sans-serif",
    allVariants: {
      color: "#404040", // Neutral Dark Gray
    },
  },
  palette: {
    primary: {
      main: "#A64D4A", // Soft Red
    },
    secondary: {
      main: "#F3F4F6", // Light Gray
    },
    text: {
      primary: "#404040", // Neutral Dark Gray
    },
    background: {
      default: "#ffffff",
      paper: "#ffffff",
    },
    error: {
      main: "#d32f2f",
    },
    // Custom colors
    accent: {
      main: "#FFE4E6", // Soft Rose
    },
    border: {
      main: "#FECACA", // Light Red
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none", // Standardize button text case
          fontWeight: 600,
        },
      },
    },
  },
});

export default theme;
