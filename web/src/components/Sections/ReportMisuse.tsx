"use client";

import React, { useState } from "react";
import axios from "axios";
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import { useTranslations } from "next-intl";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Renders a report form for submitting misuse reports and displaying submission status.
 *
 * @returns A JSX element containing the form fields (first name, last name, email, message), a submit button with a loading state, and success/error feedback alerts.
 */
export default function ReportMisuse() {
  const t = useTranslations("report");
  const tCommon = useTranslations("common");

  const [name, setName] = useState("");
  const [surname, setSurname] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; text: string } | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus(null);

    setIsSubmitting(true);
    try {
      const res = await axios.post(`${API_URL.replace(/\/+$/, "")}/support/message`, {
        name,
        surname,
        email,
        message,
      });

      if (res?.data?.status === "success") {
        setStatus({ type: "success", text: t("success") });
        setName("");
        setSurname("");
        setEmail("");
        setMessage("");
      } else {
        setStatus({ type: "error", text: res?.data?.message || t("error") });
      }
    } catch {
      setStatus({ type: "error", text: t("error") });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 6, mb: 8 }}>
      <Paper elevation={0} sx={{ borderRadius: 4, border: "1px solid", borderColor: "divider", p: 4 }}>
        <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
          {t("title")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t("subtitle")}
        </Typography>

        {status && (
          <Alert severity={status.type} sx={{ mb: 2 }}>
            {status.text}
          </Alert>
        )}

        <Box component="form" onSubmit={onSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            label={t("firstName")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label={t("lastName")}
            value={surname}
            onChange={(e) => setSurname(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label={t("email")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
            fullWidth
          />
          <TextField
            label={t("message")}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
            fullWidth
            multiline
            minRows={5}
          />

          <Button
            type="submit"
            variant="contained"
            disabled={isSubmitting}
            sx={{ mt: 1, py: 1.25, fontWeight: 700, textTransform: "none" }}
          >
            {isSubmitting ? (
              <Box sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}>
                <CircularProgress size={18} color="inherit" />
                {tCommon("loading")}
              </Box>
            ) : (
              tCommon("submit")
            )}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}