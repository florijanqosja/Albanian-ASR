"use client";
import { useState, useEffect } from "react";
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container, 
  Paper, 
  Divider, 
  InputAdornment, 
  IconButton,
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox
} from "@mui/material";
import { FcGoogle } from "react-icons/fc";
import { Eye, EyeOff, Mail, Lock, User, ArrowRight } from "lucide-react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "../../i18n/routing";
import { signIn, useSession } from "next-auth/react";
import LogoIcon from "../../src/assets/svg/Logo";
import Footer from "@/components/Sections/Footer";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Render the registration page with email and Google sign-up flows, consent collection, form validation, and navigation.
 *
 * Includes fetching the latest consent version, enforcing consent acceptance before sign-up, client-side validation (email, password length, and password confirmation), and redirects authenticated users away from the page or to the verification route after successful registration.
 *
 * @returns The registration page as a JSX element.
 */
export default function RegisterPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const t = useTranslations("register");
  const [formData, setFormData] = useState({
    name: "",
    surname: "",
    email: "",
    password: "",
    confirmPassword: ""
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [consentVersion, setConsentVersion] = useState<string | null>(null);
  const [consentId, setConsentId] = useState<number | null>(null);
  const [effectiveDate, setEffectiveDate] = useState<string | null>(null);

  // Redirect if already logged in
  useEffect(() => {
    if (status === "authenticated" && session) {
      router.push("/");
      router.refresh();
    }
  }, [status, session, router]);

  useEffect(() => {
    const fetchConsent = async () => {
      try {
        const res = await fetch(`${API_URL}/consents/latest`);
        const data = await res.json();
        if (res.ok && data?.data?.id) {
          setConsentId(data.data.id);
          setConsentVersion(data.data.version);
          setEffectiveDate(data.data.effective_date ?? null);
        } else {
          setError("Consent version missing. Please try again later.");
        }
      } catch {
        setError("Consent version missing. Please try again later.");
      }
    };
    fetchConsent();
  }, []);

  // Show loading state while checking authentication
  if (status === "loading") {
    return (
      <>
        <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50' }}>
          <CircularProgress size={40} />
        </Box>
        <Footer />
      </>
    );
  }

  // Don't render register form if already authenticated
  if (status === "authenticated") {
    return null;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    setError(null);
  };

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      setError(t("errorRequired"));
      return false;
    }
    if (formData.password.length < 8) {
      setError(t("errorLength"));
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError(t("errorMismatch"));
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    if (!consentAccepted || !consentId) {
      setError("Please accept the Terms of Service and Privacy Notice to continue.");
      return;
    }
    
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: formData.name,
          surname: formData.surname,
          email: formData.email,
          password: formData.password,
          consent_id: consentId
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || t("errorGeneric"));
      }

      router.push({ pathname: '/verify', query: { email: formData.email } });
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorGeneric"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', py: 6 }}>
        <Container component="main" maxWidth="sm">
          <Paper elevation={0} sx={{ p: 5, borderRadius: 4, border: '1px solid', borderColor: 'divider', boxShadow: '0 20px 40px -10px rgba(0,0,0,0.05)' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
              <Box sx={{ width: 60, height: 60, color: 'primary.main', mb: 2 }}>
                <LogoIcon />
              </Box>
              <Typography component="h1" variant="h4" fontWeight={800} sx={{ mb: 1 }}>
                {t("title")}
              </Typography>
              <Typography color="textSecondary">
                {t("subtitle")}
              </Typography>
            </Box>

            <Button
              fullWidth
              variant="outlined"
              size="large"
              startIcon={<FcGoogle size={24} />}
              onClick={() => {
                if (!consentAccepted || !consentId) {
                  setError("Please accept the Terms of Service and Privacy Notice to continue.");
                  return;
                }
                signIn("google", { callbackUrl: "/" })
              }}
              sx={{ 
                mb: 3, 
                py: 1.5, 
                borderRadius: 2, 
                textTransform: 'none', 
                fontSize: '1rem', 
                fontWeight: 600,
                borderColor: 'divider',
                color: 'text.primary',
                '&:hover': { bgcolor: 'grey.50', borderColor: 'grey.400' }
              }}
            >
              {t("continueGoogle")}
            </Button>

            <Divider sx={{ width: '100%', mb: 3 }}>
              <Typography variant="caption" color="textSecondary" sx={{ px: 1 }}>{t("orEmail")}</Typography>
            </Divider>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} noValidate sx={{ width: '100%' }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  margin="normal"
                  fullWidth
                  id="name"
                  label={t("firstName")}
                  name="name"
                  autoComplete="given-name"
                  autoFocus
                  value={formData.name}
                  onChange={handleChange}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <User size={20} className="text-gray-400" />
                      </InputAdornment>
                    ),
                    sx: { borderRadius: 2 }
                  }}
                />
                <TextField
                  margin="normal"
                  fullWidth
                  id="surname"
                  label={t("lastName")}
                  name="surname"
                  autoComplete="family-name"
                  value={formData.surname}
                  onChange={handleChange}
                  InputProps={{
                    sx: { borderRadius: 2 }
                  }}
                />
              </Box>

              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label={t("email")}
                name="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Mail size={20} className="text-gray-400" />
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 2 }
                }}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label={t("password")}
                type={showPassword ? "text" : "password"}
                id="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                helperText={t("passwordHint")}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock size={20} className="text-gray-400" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 2 }
                }}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label={t("confirmPassword")}
                type={showConfirmPassword ? "text" : "password"}
                id="confirmPassword"
                autoComplete="new-password"
                value={formData.confirmPassword}
                onChange={handleChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock size={20} className="text-gray-400" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle confirm password visibility"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        edge="end"
                      >
                        {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 2 }
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading || !consentAccepted || !consentId}
                endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowRight size={20} />}
                sx={{ 
                  mt: 4, 
                  mb: 3, 
                  py: 1.5, 
                  borderRadius: 2, 
                  fontWeight: 700,
                  boxShadow: (theme) => theme.shadows[4]
                }}
              >
                {loading ? t("creating") : t("cta")}
              </Button>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={consentAccepted}
                    onChange={(event) => setConsentAccepted(event.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2" color="textSecondary">
                    I have read and agree to the{' '}
                    <Link href="/termsandservices" className="font-bold text-primary hover:underline">
                      Terms of Service
                    </Link>{' '}and{' '}
                    <Link href="/privacy" className="font-bold text-primary hover:underline">
                      Privacy Notice
                    </Link>
                    {consentVersion ? ` (Version ${consentVersion}${effectiveDate ? `, effective ${effectiveDate}` : ''})` : ''}.
                  </Typography>
                }
                sx={{ alignItems: 'flex-start', mb: 2 }}
              />
              
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary">
                  {t("already")}{' '}
                  <Link href="/login" className="font-bold text-primary hover:underline">
                    {t("signin")}
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Container>
      </Box>
      <Footer />
    </>
  );
}