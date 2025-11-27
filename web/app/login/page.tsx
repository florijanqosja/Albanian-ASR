"use client"
import { useState } from "react"
import { signIn } from "next-auth/react"
import { Box, Button, TextField, Typography, Container, Paper, Divider, InputAdornment, IconButton } from "@mui/material"
import { FcGoogle } from "react-icons/fc"
import { Eye, EyeOff, Mail, Lock, ArrowRight } from "lucide-react"
import Link from "next/link"
import LogoIcon from "../../src/assets/svg/Logo"
import Footer from "@/components/Sections/Footer"

const isProduction = process.env.NEXT_PUBLIC_ENVIRONMENT === "production"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    await signIn("credentials", { email, password, callbackUrl: "/" })
    setLoading(false)
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
              Welcome Back
            </Typography>
            <Typography color="textSecondary">
              Sign in to continue to DibraSpeaks
            </Typography>
          </Box>
          
          {isProduction && (
            <>
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
            </>
          )}

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
              onChange={(e) => setEmail(e.target.value)}
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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              endIcon={<ArrowRight size={20} />}
              sx={{ 
                mt: 4, 
                mb: 3, 
                py: 1.5, 
                borderRadius: 2, 
                fontWeight: 700,
                boxShadow: '0 4px 14px 0 rgba(166, 77, 74, 0.39)'
              }}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
            
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Link href="/forgot-password" className="text-gray-500 hover:text-primary text-sm">
                Forgot your password?
              </Link>
            </Box>

            <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="textSecondary">
                    Don&apos;t have an account?{' '}
                    <Link href="/register" className="font-bold text-primary hover:underline">
                        Sign up
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
