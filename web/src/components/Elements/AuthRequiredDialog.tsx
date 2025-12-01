"use client"
import { Dialog, Box, Typography, Button } from "@mui/material"
import { alpha, useTheme } from "@mui/material/styles"
import LogoIcon from "@/assets/svg/Logo"

interface AuthRequiredDialogProps {
  open: boolean
  onClose: () => void
  onSkip: () => void
  onAuthenticate: () => void
  message?: string
}

export default function AuthRequiredDialog({ open, onClose, onSkip, onAuthenticate, message }: AuthRequiredDialogProps) {
  const theme = useTheme()
  const dialogMessage = message ?? "Please register or log in to keep track of your contributions. You can also continue anonymously if you prefer."

  return (
    <Dialog
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
          maxWidth: 420,
          width: "100%",
          boxShadow: `0 30px 70px ${alpha(theme.palette.common.black, 0.12)}`,
          backgroundColor: theme.palette.background.paper,
        },
      }}
    >
      <Box sx={{ px: 5, pt: 4, pb: 2, textAlign: "center" }}>
        <Box sx={{ width: 56, height: 56, mx: "auto", mb: 2, color: "primary.main" }}>
          <LogoIcon />
        </Box>
        <Typography variant="h5" fontWeight={800} gutterBottom>
          Authentication Required
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {dialogMessage}
        </Typography>
      </Box>
      <Box sx={{ px: 5, pb: 4, display: "flex", flexDirection: "column", gap: 1.5 }}>
        <Button
          variant="contained"
          size="large"
          onClick={onAuthenticate}
          sx={{
            borderRadius: 2,
            fontWeight: 700,
            textTransform: "none",
            boxShadow: `0 12px 30px ${alpha(theme.palette.primary.main, 0.25)}`,
          }}
        >
          Register / Log In
        </Button>
        <Button
          variant="text"
          size="large"
          onClick={onSkip}
          sx={{ fontWeight: 600, textTransform: "none", color: "text.secondary" }}
        >
          Continue anonymously
        </Button>
      </Box>
    </Dialog>
  )
}
