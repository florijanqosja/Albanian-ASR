"use client"
import { useState, useEffect, useRef, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Link, useRouter } from "../../i18n/routing"
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container, 
  Paper, 
  Alert,
  CircularProgress
} from "@mui/material"
import { Mail, ArrowRight, RefreshCw } from "lucide-react"
import LogoIcon from "../../src/assets/svg/Logo"
import Footer from "@/components/Sections/Footer"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function VerifyPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get("email") || ""
  
  const [code, setCode] = useState(["", "", "", "", "", ""])
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Focus first input on mount
  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  const handleInputChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return

    const newCode = [...code]
    newCode[index] = value
    setCode(newCode)
    setError(null)

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit when all digits are entered
    if (value && index === 5 && newCode.every(digit => digit !== "")) {
      handleSubmit(newCode.join(""))
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6)
    if (pastedData.length === 6) {
      const newCode = pastedData.split("")
      setCode(newCode)
      inputRefs.current[5]?.focus()
      handleSubmit(pastedData)
    }
  }

  const handleSubmit = async (verificationCode?: string) => {
    const codeToSubmit = verificationCode || code.join("")
    
    if (codeToSubmit.length !== 6) {
      setError("Please enter the complete 6-digit code")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/auth/verify-email`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email: email,
          code: codeToSubmit
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Verification failed")
      }

      // Verification successful - show success and redirect to login
      setSuccess("Email verified successfully! Redirecting to login...")
      
      // Redirect to login page after a short delay
      setTimeout(() => {
        router.push({ pathname: '/login', query: { verified: 'true', email } })
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed")
      setCode(["", "", "", "", "", ""])
      inputRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    setResending(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${API_URL}/auth/resend-verification`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Failed to resend code")
      }

      setSuccess("A new verification code has been sent to your email")
      setCode(["", "", "", "", "", ""])
      inputRefs.current[0]?.focus()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend code")
    } finally {
      setResending(false)
    }
  }

  if (!email) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', py: 12 }}>
        <Container component="main" maxWidth="sm">
          <Paper elevation={0} sx={{ p: 5, borderRadius: 4, border: '1px solid', borderColor: 'divider', textAlign: 'center' }}>
            <Typography variant="h6" color="error" sx={{ mb: 2 }}>
              No email address provided
            </Typography>
            <Button component={Link} href="/register" variant="contained">
              Go to Registration
            </Button>
          </Paper>
        </Container>
      </Box>
    )
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
                Verify Your Email
              </Typography>
              <Typography color="textSecondary" sx={{ textAlign: 'center' }}>
                We sent a 6-digit code to
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <Mail size={18} className="text-gray-500" />
                <Typography fontWeight={600} color="primary.main">
                  {email}
                </Typography>
              </Box>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                {success}
              </Alert>
            )}

            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1.5, mb: 4 }} onPaste={handlePaste}>
              {code.map((digit, index) => (
                <TextField
                  key={index}
                  inputRef={el => inputRefs.current[index] = el}
                  value={digit}
                  onChange={(e) => handleInputChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  inputProps={{
                    maxLength: 1,
                    style: { 
                      textAlign: 'center', 
                      fontSize: '1.5rem', 
                      fontWeight: 700,
                      padding: '12px'
                    }
                  }}
                  sx={{ 
                    width: 56,
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      '&.Mui-focused': {
                        '& fieldset': {
                          borderColor: 'primary.main',
                          borderWidth: 2
                        }
                      }
                    }
                  }}
                  disabled={loading}
                />
              ))}
            </Box>

            <Button
              fullWidth
              variant="contained"
              size="large"
              disabled={loading || code.some(d => d === "")}
              onClick={() => handleSubmit()}
              endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowRight size={20} />}
              sx={{ 
                mb: 3, 
                py: 1.5, 
                borderRadius: 2, 
                fontWeight: 700,
                boxShadow: '0 4px 14px 0 rgba(166, 77, 74, 0.39)'
              }}
            >
              {loading ? "Verifying..." : "Verify Email"}
            </Button>

            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                Didn&apos;t receive the code?
              </Typography>
              <Button
                variant="text"
                startIcon={resending ? <CircularProgress size={16} /> : <RefreshCw size={16} />}
                onClick={handleResend}
                disabled={resending}
                sx={{ textTransform: 'none', fontWeight: 600 }}
              >
                {resending ? "Sending..." : "Resend Code"}
              </Button>
            </Box>

            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Typography variant="body2" color="textSecondary">
                Wrong email?{' '}
                <Link href="/register" className="font-bold text-primary hover:underline">
                  Go back
                </Link>
              </Typography>
            </Box>
          </Paper>
        </Container>
      </Box>
      <Footer />
    </>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    }>
      <VerifyPageContent />
    </Suspense>
  )
}
