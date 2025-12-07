"use client"
import { useState } from "react"
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container, 
  Paper, 
  InputAdornment,
  Alert,
  CircularProgress
} from "@mui/material"
import { Mail, ArrowRight, ArrowLeft } from "lucide-react"
import { Link, useRouter } from "../../i18n/routing"
import LogoIcon from "../../src/assets/svg/Logo"
import Footer from "@/components/Sections/Footer"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function ForgotPasswordPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) {
      setError("Please enter your email address")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Failed to send reset code")
      }

      setSuccess(true)
      
      // Redirect to reset password page after a short delay
      setTimeout(() => {
        router.push({ pathname: '/reset-password', query: { email } })
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reset code")
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', py: 12 }}>
        <Container component="main" maxWidth="sm">
          <Paper elevation={0} sx={{ p: 5, borderRadius: 4, border: '1px solid', borderColor: 'divider', boxShadow: '0 20px 40px -10px rgba(0,0,0,0.05)' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
              <Box sx={{ width: 60, height: 60, color: 'primary.main', mb: 2 }}>
                <LogoIcon />
              </Box>
              <Typography component="h1" variant="h4" fontWeight={800} sx={{ mb: 1 }}>
                Forgot Password?
              </Typography>
              <Typography color="textSecondary" sx={{ textAlign: 'center' }}>
                No worries! Enter your email and we&apos;ll send you a reset code.
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            {success ? (
              <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                If an account with that email exists, a password reset code has been sent. Redirecting...
              </Alert>
            ) : (
              <Box component="form" onSubmit={handleSubmit} noValidate sx={{ width: '100%' }}>
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="email"
                  label="Email Address"
                  name="email"
                  autoComplete="email"
                  autoFocus
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    setError(null)
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Mail size={20} className="text-gray-400" />
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
                  disabled={loading}
                  endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowRight size={20} />}
                  sx={{ 
                    mt: 4, 
                    mb: 3, 
                    py: 1.5, 
                    borderRadius: 2, 
                    fontWeight: 700,
                    boxShadow: '0 4px 14px 0 rgba(166, 77, 74, 0.39)'
                  }}
                >
                  {loading ? "Sending..." : "Send Reset Code"}
                </Button>
              </Box>
            )}
            
            <Box sx={{ textAlign: 'center' }}>
              <Link href="/login" className="inline-flex items-center gap-1 text-gray-500 hover:text-primary">
                <ArrowLeft size={16} />
                <Typography variant="body2">
                  Back to Sign In
                </Typography>
              </Link>
            </Box>
          </Paper>
        </Container>
      </Box>
      <Footer />
    </>
  )
}
