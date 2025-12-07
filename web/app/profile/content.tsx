"use client"
import { useSession } from "next-auth/react"
import { useState, useEffect } from "react"
import type { ChangeEvent } from "react"
import { Container, Typography, TextField, Button, Box, Paper, Grid, Avatar, Divider, MenuItem } from "@mui/material"
import { User, Mail, Phone, MapPin, Globe, Mic, Save } from "lucide-react"
import axios from "axios"
import Footer from "@/components/Sections/Footer"
import { ALBANIAN_ACCENTS, ALBANIAN_REGIONS, ACCENT_OTHER_VALUE, REGION_OTHER_VALUE } from "@/constants/profileOptions"

export default function ProfilePage() {
  const { data: session } = useSession()
  const [formData, setFormData] = useState({
    name: "",
    surname: "",
    email: "",
    phone_number: "",
    age: "",
    nationality: "",
    accent: "",
    region: ""
  })
  const [loading, setLoading] = useState(false)
  const [accentSelection, setAccentSelection] = useState("")
  const [customAccent, setCustomAccent] = useState("")
  const [regionSelection, setRegionSelection] = useState("")
  const [customRegion, setCustomRegion] = useState("")

    const handleAccentSelection = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const value = event.target.value
        setAccentSelection(value)
        if (value === ACCENT_OTHER_VALUE) {
            setFormData(prev => ({ ...prev, accent: customAccent }))
        } else {
            setCustomAccent("")
            setFormData(prev => ({ ...prev, accent: value }))
        }
    }

    const handleRegionSelection = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const value = event.target.value
        setRegionSelection(value)
        if (value === REGION_OTHER_VALUE) {
            setFormData(prev => ({ ...prev, region: customRegion }))
        } else {
            setCustomRegion("")
            setFormData(prev => ({ ...prev, region: value }))
        }
    }

  useEffect(() => {
    if (session?.user) {
        const fetchUser = async () => {
            try {
                const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/me`, {
                    headers: { Authorization: `Bearer ${(session as { accessToken?: string }).accessToken}` }
                })
                setFormData(res.data)
                const accentValue = res.data.accent || ""
                if (accentValue && !ALBANIAN_ACCENTS.includes(accentValue)) {
                    setAccentSelection(ACCENT_OTHER_VALUE)
                    setCustomAccent(accentValue)
                } else {
                    setAccentSelection(accentValue || "")
                    setCustomAccent("")
                }

                const regionValue = res.data.region || ""
                if (regionValue && !ALBANIAN_REGIONS.includes(regionValue)) {
                    setRegionSelection(REGION_OTHER_VALUE)
                    setCustomRegion(regionValue)
                } else {
                    setRegionSelection(regionValue || "")
                    setCustomRegion("")
                }
            } catch (e) {
                console.error(e)
            }
        }
        fetchUser()
    }
  }, [session])

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
        if (accentSelection === ACCENT_OTHER_VALUE && !customAccent.trim()) {
            alert("Please specify your accent/dialect")
            setLoading(false)
            return
        }

        await axios.put(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/me`, formData, {
            headers: { Authorization: `Bearer ${(session as { accessToken?: string }).accessToken}` }
        })
        alert("Profile updated successfully!")
    } catch {
        alert("Error updating profile")
    } finally {
        setLoading(false)
    }
  }

  if (!session) return (
    <Container sx={{ mt: 10, textAlign: 'center' }}>
        <Typography variant="h5" color="textSecondary">Please log in to view your profile.</Typography>
    </Container>
  )

  return (
    <>
    <Container maxWidth="md" sx={{ mt: 6, mb: 8 }}>
      <Paper elevation={0} sx={{ borderRadius: 4, border: '1px solid', borderColor: 'divider', overflow: 'hidden' }}>
        <Box sx={{ bgcolor: 'primary.main', height: 120, position: 'relative' }}>
            <Box sx={{ position: 'absolute', bottom: -40, left: 40, p: 0.5, bgcolor: 'white', borderRadius: '50%' }}>
                <Avatar 
                    src={session.user?.image || undefined} 
                    sx={{ width: 100, height: 100, border: '4px solid white' }}
                />
            </Box>
        </Box>
        
        <Box sx={{ pt: 6, px: 5, pb: 5 }}>
            <Box sx={{ mb: 4, ml: 14 }}>
                <Typography variant="h4" fontWeight={800}>{session.user?.name}</Typography>
                <Typography variant="body1" color="textSecondary">{session.user?.email}</Typography>
            </Box>

            <Divider sx={{ mb: 4 }} />

            <Box component="form" onSubmit={handleSubmit}>
                <Typography variant="h6" fontWeight={700} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <User size={20} /> Personal Information
                </Typography>
                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="First Name" 
                            name="name" 
                            value={formData.name || ""} 
                            onChange={handleChange}
                            variant="outlined"
                            InputProps={{ sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="Last Name" 
                            name="surname" 
                            value={formData.surname || ""} 
                            onChange={handleChange}
                            variant="outlined"
                            InputProps={{ sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="Email" 
                            name="email" 
                            value={formData.email || ""} 
                            disabled 
                            variant="filled"
                            InputProps={{ startAdornment: <Mail size={18} style={{ marginRight: 8, opacity: 0.5 }} />, sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="Phone Number" 
                            name="phone_number" 
                            value={formData.phone_number || ""} 
                            onChange={handleChange}
                            variant="outlined"
                            InputProps={{ startAdornment: <Phone size={18} style={{ marginRight: 8, opacity: 0.5 }} />, sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="Age" 
                            name="age" 
                            type="number" 
                            value={formData.age || ""} 
                            onChange={handleChange}
                            variant="outlined"
                            InputProps={{ sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField 
                            fullWidth 
                            label="Nationality" 
                            name="nationality" 
                            value={formData.nationality || ""} 
                            onChange={handleChange}
                            variant="outlined"
                            InputProps={{ startAdornment: <Globe size={18} style={{ marginRight: 8, opacity: 0.5 }} />, sx: { borderRadius: 2 } }}
                        />
                    </Grid>
                </Grid>

                <Typography variant="h6" fontWeight={700} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Mic size={20} /> Linguistic Profile
                </Typography>
                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                            select
                            fullWidth
                            label="Accent / Dialect"
                            name="accent"
                            value={accentSelection}
                            onChange={handleAccentSelection}
                            helperText="Choose the dialect that best matches your speech"
                            variant="outlined"
                            InputProps={{ sx: { borderRadius: 2 } }}
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
                                label="Custom Accent / Dialect"
                                value={customAccent}
                                onChange={(event) => {
                                    const value = event.target.value
                                    setCustomAccent(value)
                                    setFormData(prev => ({ ...prev, accent: value }))
                                }}
                                sx={{ mt: 2 }}
                                helperText="Please describe your dialect"
                                required
                                InputProps={{ sx: { borderRadius: 2 } }}
                            />
                        )}
                    </Grid>
                    <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                            select
                            fullWidth
                            label="Region"
                            name="region"
                            value={regionSelection}
                            onChange={handleRegionSelection}
                            helperText="Where do you primarily speak Albanian?"
                            variant="outlined"
                            InputProps={{ startAdornment: <MapPin size={18} style={{ marginRight: 8, opacity: 0.5 }} />, sx: { borderRadius: 2 } }}
                        >
                            <MenuItem value="">
                                <em>Select your region</em>
                            </MenuItem>
                            {ALBANIAN_REGIONS.map(region => (
                                <MenuItem key={region} value={region}>
                                    {region}
                                </MenuItem>
                            ))}
                            <MenuItem value={REGION_OTHER_VALUE}>Other / Custom</MenuItem>
                        </TextField>
                        {regionSelection === REGION_OTHER_VALUE && (
                            <TextField
                                fullWidth
                                label="Custom Region"
                                value={customRegion}
                                onChange={(event) => {
                                    const value = event.target.value
                                    setCustomRegion(value)
                                    setFormData(prev => ({ ...prev, region: value }))
                                }}
                                sx={{ mt: 2 }}
                                helperText="Add your city or region"
                                InputProps={{ sx: { borderRadius: 2 } }}
                            />
                        )}
                    </Grid>
                </Grid>

                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button 
                        type="submit" 
                        variant="contained" 
                        size="large"
                        disabled={loading}
                        startIcon={<Save size={18} />}
                        sx={{ 
                            px: 4, 
                            py: 1.5, 
                            borderRadius: 2, 
                            fontWeight: 700,
                            boxShadow: '0 4px 14px 0 rgba(166, 77, 74, 0.39)'
                        }}
                    >
                        {loading ? "Saving..." : "Save Changes"}
                    </Button>
                </Box>
            </Box>
        </Box>
      </Paper>
    </Container>
    <Footer />
    </>
  )
}
