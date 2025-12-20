"use client";
import React, { ComponentProps } from "react";
import { Github, Linkedin, ArrowUp } from "lucide-react";
import {
  Container,
  Grid,
  Typography,
  IconButton,
  Box,
  Stack,
  Button,
  Divider,
  Link as MuiLink,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useTranslations } from "next-intl";
import { Link } from "../../../i18n/routing";
import LogoImg from "../../assets/svg/Logo";

export default function Footer() {
  const t = useTranslations("footer");
  const tCommon = useTranslations("common");
  const theme = useTheme();
  const docsUrl = process.env.NEXT_PUBLIC_API_DOCS_URL || "http://localhost:8000/docs";

  type AppLinkHref = ComponentProps<typeof Link>["href"];

  const navLinks: Array<{ href: AppLinkHref; label: string }> = [
    { href: "/termsandservices", label: t("terms") },
    { href: "/report", label: t("report") },
    { href: "/privacy", label: t("privacy") },
  ];

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const linkStyles = {
    color: "text.secondary",
    fontWeight: 600,
    textDecoration: "none",
    display: "inline-flex",
    alignItems: "center",
    gap: 0.5,
    transition: "color 0.2s ease",
    "&:hover": { color: "primary.main" },
  } as const;

  const iconButtonStyles = {
    border: `1px solid ${alpha(theme.palette.primary.main, 0.18)}`,
    color: "text.secondary",
    bgcolor: alpha(theme.palette.background.paper, 0.92),
    transition: "all 0.2s ease",
    "&:hover": {
      bgcolor: alpha(theme.palette.primary.main, 0.08),
      color: "primary.main",
      borderColor: theme.palette.primary.main,
    },
  } as const;

  return (
    <Box
      component="footer"
      sx={{
        mt: "auto",
        bgcolor: alpha(theme.palette.primary.main, 0.06),
        borderTop: `1px solid ${alpha(theme.palette.primary.main, 0.12)}`,
        px: 2,
        py: { xs: 4, md: 6 },
        position: "relative",
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 15% 30%, ${alpha(
            theme.palette.accent.main,
            0.8
          )}, transparent 35%), radial-gradient(circle at 85% 10%, ${alpha(
            theme.palette.primary.main,
            0.18
          )}, transparent 30%)`,
          pointerEvents: "none",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative" }}>
        <Grid container spacing={{ xs: 4, md: 6 }} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <Stack spacing={2.5}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Box sx={{ width: 44, height: 44, color: "primary.main" }}>
                  <LogoImg />
                </Box>
                <Typography variant="h5" fontWeight={800} color="text.primary">
                  DibraSpeaks
                </Typography>
              </Box>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 440 }}>
                {t("tagline")}
              </Typography>
              <Stack direction="row" spacing={1.25}>
                <IconButton
                  component="a"
                  href="https://github.com/florijanqosja/Albanian-ASR"
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={iconButtonStyles}
                >
                  <Github size={20} />
                </IconButton>
                <IconButton
                  component="a"
                  href="https://www.linkedin.com/in/florijan-qosja/"
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={iconButtonStyles}
                >
                  <Linkedin size={20} />
                </IconButton>
              </Stack>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Stack spacing={1.2} alignItems={{ xs: "flex-start", md: "flex-end" }}>
              {navLinks.map((item) => (
                <MuiLink
                  key={item.href.toString()}
                  component={Link}
                  href={item.href}
                  underline="none"
                  sx={linkStyles}
                >
                  <Typography variant="body2" component="span">
                    {item.label}
                  </Typography>
                </MuiLink>
              ))}
              {docsUrl && (
                <Typography
                  component="a"
                  href={docsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="body2"
                  sx={linkStyles}
                >
                  {t("apiDocs")}
                </Typography>
              )}
            </Stack>
          </Grid>
        </Grid>

        <Divider sx={{ my: { xs: 3, md: 4 }, borderColor: alpha(theme.palette.border.main, 0.6) }} />

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {t("copyright")}
          </Typography>
          <Button
            onClick={scrollToTop}
            variant="contained"
            color="primary"
            startIcon={<ArrowUp size={16} />}
            sx={{
              borderRadius: 999,
              px: 2.5,
              boxShadow: "none",
              fontWeight: 700,
              "&:hover": { boxShadow: "none" },
            }}
          >
            {tCommon("backToTop")}
          </Button>
        </Box>
      </Container>
    </Box>
  );
}
