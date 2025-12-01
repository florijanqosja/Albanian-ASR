"use client";
import React from "react";
import Link from "next/link";
import LogoImg from "../../assets/svg/Logo";
import { Github, Linkedin, ArrowUp } from "lucide-react";
import { Container, Grid, Typography, IconButton, Box } from "@mui/material";

export default function Footer() {
  const docsUrl = process.env.NEXT_PUBLIC_API_DOCS_URL || "http://localhost:8000/docs";
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Box component="footer" sx={{ bgcolor: '#1F2937', color: 'white', py: 6, mt: 'auto' }}>
      <Container maxWidth="lg">
        <Grid container spacing={4} alignItems="center" justifyContent="space-between">
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Box sx={{ width: 40, height: 40, color: 'primary.main' }}>
                <LogoImg />
              </Box>
              <Typography variant="h5" fontWeight={700} sx={{ background: 'linear-gradient(45deg, #A64D4A, #FF8E53)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                DibraSpeaks
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ color: 'grey.400', maxWidth: 300 }}>
              Building the future of Albanian speech technology, one voice at a time.
            </Typography>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }} sx={{ textAlign: { xs: 'left', md: 'center' } }}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: { xs: 'flex-start', md: 'center' }, mb: 2 }}>
              <IconButton 
                component="a" 
                href="https://github.com/florijanqosja" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ color: 'grey.400', '&:hover': { color: 'white', bgcolor: 'rgba(255,255,255,0.1)' } }}
              >
                <Github size={24} />
              </IconButton>
              <IconButton 
                component="a" 
                href="https://www.linkedin.com/in/florijan-qosja/" 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ color: 'grey.400', '&:hover': { color: '#0077b5', bgcolor: 'rgba(0,119,181,0.1)' } }}
              >
                <Linkedin size={24} />
              </IconButton>
            </Box>
            <Link href="/termsandservices" className="text-gray-400 hover:text-white text-sm transition-colors">
              Terms and Conditions
            </Link>
            {docsUrl && (
              <a
                href={docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-gray-400 hover:text-white text-sm transition-colors mt-1"
              >
                API Docs
              </a>
            )}
            <Typography variant="body2" sx={{ color: 'grey.500', mt: 1 }}>
              © 2025 DibraSpeaks. All rights reserved.
            </Typography>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
            <Box 
              onClick={scrollToTop}
              sx={{ 
                display: 'inline-flex', 
                alignItems: 'center', 
                gap: 1, 
                cursor: 'pointer', 
                color: 'grey.400', 
                '&:hover': { color: 'primary.main' },
                transition: 'color 0.2s'
              }}
            >
              <Typography variant="button" sx={{ textTransform: 'none', color: 'inherit' }}>Back to top</Typography>
              <ArrowUp size={16} />
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}
