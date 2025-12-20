"use client"
import { useEffect, useState } from "react"
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Button,
  IconButton,
  TextField,
  Typography,
  InputAdornment,
  MenuItem,
  CircularProgress,
  Alert,
  Checkbox,
  FormControlLabel
} from "@mui/material"
import { Phone, MapPin, Globe, User, ArrowRight, X } from "lucide-react"
import Link from "next/link"
import LogoIcon from "../../assets/svg/Logo"
import { ALBANIAN_REGIONS, ALBANIAN_ACCENTS, ACCENT_OTHER_VALUE } from "@/constants/profileOptions"
import { Theme } from "@mui/material/styles"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ProfileCompletionModalProps {
  open: boolean
  accessToken: string
  userName?: string
  onClose: () => void
  onComplete: () => void
}

/**
 * Modal dialog that prompts the user to complete optional profile fields and accept consent before continuing.
 *
 * Renders a form for phone number, age, nationality, region and Albanian dialect/accent (with a custom option),
 * fetches the latest consent metadata on mount, requires the user to accept the Terms of Service and Privacy Notice,
 * and submits profile data (including `consent_id`) to the server. Provides controls to save the profile or dismiss the modal.
 *
 * @param open - Controls whether the dialog is visible
 * @param accessToken - Bearer token used for authenticated API requests
 * @param onComplete - Called when the profile is successfully saved
 * @param onClose - Called when the modal is dismissed/closed
 * @param userName - Optional user display name shown in the welcome message
 * @returns The profile completion modal React element
 */
export default function ProfileCompletionModal({ 
  open, 
  accessToken, 
  onComplete,
  onClose,
  userName
}: ProfileCompletionModalProps) {
  const [formData, setFormData] = useState({
    phone_number: "",
    age: "",
    nationality: "Albanian",
    accent: "",
    region: ""
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [accentSelection, setAccentSelection] = useState<string>("")
  const [customAccent, setCustomAccent] = useState("")
  const [consentAccepted, setConsentAccepted] = useState(false)
  const [consentId, setConsentId] = useState<number | null>(null)
  const [consentVersion, setConsentVersion] = useState<string | null>(null)
  const [effectiveDate, setEffectiveDate] = useState<string | null>(null)

  useEffect(() => {
    const fetchConsent = async () => {
      try {
        const res = await fetch(`${API_URL}/consents/latest`)
        const data = await res.json()
        if (res.ok && data?.data?.id) {
          setConsentId(data.data.id)
          setConsentVersion(data.data.version)
          setEffectiveDate(data.data.effective_date ?? null)
        } else {
          setError("Consent version missing. Please try again later.")
        }
      } catch {
        setError("Consent version missing. Please try again later.")
      }
    }

    fetchConsent()
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
    setError(null)
  }

  const handleAccentSelection = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const value = event.target.value
    setAccentSelection(value)
    if (value === ACCENT_OTHER_VALUE) {
      setFormData(prev => ({ ...prev, accent: customAccent }))
    } else {
      setCustomAccent("")
      setFormData(prev => ({ ...prev, accent: value }))
    }
    setError(null)
  }

  const handleCustomAccentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value
    setCustomAccent(value)
    if (accentSelection === ACCENT_OTHER_VALUE) {
      setFormData(prev => ({ ...prev, accent: value }))
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError(null)

    try {
      if (accentSelection === ACCENT_OTHER_VALUE && !formData.accent?.trim()) {
        throw new Error("Please specify your dialect when choosing Other")
      }

      if (!consentAccepted || !consentId) {
        throw new Error("Please accept the Terms of Service and Privacy Notice to continue.")
      }

      const response = await fetch(`${API_URL}/users/complete-profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          phone_number: formData.phone_number || null,
          age: formData.age ? parseInt(formData.age) : null,
          nationality: formData.nationality || null,
          accent: formData.accent || null,
          region: formData.region || null,
          consent_id: consentId
        })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || "Failed to save profile")
      }

      onComplete()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile")
    } finally {
      setLoading(false)
    }
  }

  const handleDismiss = async () => {
    try {
      if (consentId) {
        await fetch(`${API_URL}/users/complete-profile`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`
          },
          body: JSON.stringify({ consent_id: consentId })
        })
      }
    } catch (err) {
      console.error("Failed to mark profile complete on dismiss", err)
    } finally {
      onClose()
    }
  }

  return (
    <Dialog 
      open={open} 
      maxWidth="sm" 
      fullWidth
      onClose={handleDismiss}
      PaperProps={{
        sx: {
          borderRadius: 4,
          border: '1px solid',
          borderColor: 'divider',
          boxShadow: (theme: Theme) => theme.shadows[10]
        }
      }}
    >
      <DialogTitle sx={{ pb: 1.5 }}>
        <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
          <IconButton aria-label="Close" onClick={handleDismiss} size="small">
            <X size={18} />
          </IconButton>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 2 }}>
          <Box sx={{ width: 50, height: 50, color: 'primary.main', mb: 2 }}>
            <LogoIcon />
          </Box>
          <Typography variant="h5" fontWeight={800} sx={{ mb: 0.5 }}>
            Welcome{userName ? `, ${userName}` : ''}! 🎉
          </Typography>
          <Typography
            color="textSecondary"
            variant="body2"
            sx={{ textAlign: 'center', mt: 0.5, mb: 2.5, px: 2 }}
          >
            Help us personalize your experience by completing your profile
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            fullWidth
            label="Phone Number"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleChange}
            placeholder="+355 6X XXX XXXX"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Phone size={20} className="text-gray-400" />
                </InputAdornment>
              ),
              sx: { borderRadius: 2 }
            }}
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              label="Age"
              name="age"
              type="number"
              value={formData.age}
              onChange={handleChange}
              inputProps={{ min: 13, max: 120 }}
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
              fullWidth
              label="Nationality"
              name="nationality"
              value={formData.nationality}
              onChange={handleChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Globe size={20} className="text-gray-400" />
                  </InputAdornment>
                ),
                sx: { borderRadius: 2 }
              }}
            />
          </Box>

          <TextField
            select
            fullWidth
            label="Region"
            name="region"
            value={formData.region}
            onChange={handleChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <MapPin size={20} className="text-gray-400" />
                </InputAdornment>
              ),
              sx: { borderRadius: 2 }
            }}
          >
            <MenuItem value="">
              <em>Select your region</em>
            </MenuItem>
            {ALBANIAN_REGIONS.map(region => (
              <MenuItem key={region} value={region}>
                {region}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            fullWidth
            label="Albanian Dialect/Accent"
            name="accent"
            value={accentSelection}
            onChange={handleAccentSelection}
            helperText="This helps us improve speech recognition for different dialects"
            InputProps={{
              sx: { borderRadius: 2 }
            }}
          >
            <MenuItem value="">
              <em>Select your dialect</em>
            </MenuItem>
            {ALBANIAN_ACCENTS.map(accent => (
              <MenuItem key={accent} value={accent}>
                {accent}
              </MenuItem>
            ))}
            <MenuItem value={ACCENT_OTHER_VALUE}>Other / Custom</MenuItem>
          </TextField>

          {accentSelection === ACCENT_OTHER_VALUE && (
            <TextField
              fullWidth
              label="Custom Dialect"
              value={customAccent}
              onChange={handleCustomAccentChange}
              placeholder="Describe your dialect"
              InputProps={{ sx: { borderRadius: 2 } }}
              helperText="Please specify your dialect"
            />
          )}
        </Box>

        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 2, textAlign: 'center' }}>
          All fields are optional. You can update this information later in your profile settings.
        </Typography>

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
          sx={{ alignItems: 'flex-start', mt: 2 }}
        />
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button
          fullWidth
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={loading || !consentAccepted || !consentId}
          endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowRight size={20} />}
          sx={{
            py: 1.5,
            borderRadius: 2,
            fontWeight: 700,
            boxShadow: (theme) => theme.shadows[4]
          }}
        >
          {loading ? "Saving..." : "Complete Profile"}
        </Button>
      </DialogActions>
    </Dialog>
  )
}