"use client";
import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  typography: {
    fontFamily: "var(--font-khula), sans-serif",
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
    // Custom colors can be added via module augmentation if needed, 
    // but for now we map to standard palette slots where possible.
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
