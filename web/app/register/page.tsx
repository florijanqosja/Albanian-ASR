"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
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
  CircularProgress
} from "@mui/material"
import { FcGoogle } from "react-icons/fc"
import { Eye, EyeOff, Mail, Lock, User, ArrowRight } from "lucide-react"
import Link from "next/link"
import { signIn } from "next-auth/react"
import LogoIcon from "../../src/assets/svg/Logo"
import Footer from "@/components/Sections/Footer"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    name: "",
    surname: "",
    email: "",
    password: "",
    confirmPassword: ""
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
    setError(null)
  }

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      setError("Email and password are required")
      return false
    }
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters")
      return false
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match")
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    
    setLoading(true)
    setError(null)

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
          password: formData.password
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed")
      }

      // Redirect to verification page with email
      router.push(`/verify?email=${encodeURIComponent(formData.email)}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed")
    } finally {
      setLoading(false)
    }
  }

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
                Create Account
              </Typography>
              <Typography color="textSecondary">
                Join DibraSpeaks and help build Albanian ASR
              </Typography>
            </Box>

            <Button
              fullWidth
              variant="outlined"
              size="large"
              startIcon={<FcGoogle size={24} />}
              onClick={() => signIn("google", { callbackUrl: "/" })}
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
              Continue with Google
            </Button>

            <Divider sx={{ width: '100%', mb: 3 }}>
              <Typography variant="caption" color="textSecondary" sx={{ px: 1 }}>OR EMAIL</Typography>
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
                  label="First Name"
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
                  label="Last Name"
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
                label="Email Address"
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
                label="Password"
                type={showPassword ? "text" : "password"}
                id="password"
                autoComplete="new-password"
                value={formData.password}
                onChange={handleChange}
                helperText="At least 8 characters"
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
                label="Confirm Password"
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
                {loading ? "Creating account..." : "Create Account"}
              </Button>

              <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', mb: 2 }}>
                By creating an account, you agree to our{' '}
                <Link href="/termsandservices" className="font-bold text-primary hover:underline">
                  Terms of Service
                </Link>
              </Typography>
              
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary">
                  Already have an account?{' '}
                  <Link href="/login" className="font-bold text-primary hover:underline">
                    Sign in
                  </Link>
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Container>
      </Box>
      <Footer />
    </>
  )
}
