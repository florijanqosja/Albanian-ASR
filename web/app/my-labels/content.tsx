"use client"
import { useSession } from "next-auth/react"
import { useState, useEffect, ChangeEvent, ReactNode, useCallback } from "react"
import { Container, Typography, Paper, Grid, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Chip, TextField, Button, FormControlLabel, Checkbox, Alert, TablePagination, CircularProgress } from "@mui/material"
import { alpha } from "@mui/material/styles"
import { CheckCircle, Mic, Clock, Activity, Edit3, Timer } from "lucide-react"
import axios from "axios"
import Footer from "@/components/Sections/Footer"
import { buildFileAccessUrl } from "@/lib/utils"
import Link from "next/link"

interface UploadStats {
  total_generated: number;
  validated_count: number;
  labeled_count: number;
  unlabeled_count: number;
}

interface ActivityItem {
  id: number;
  name?: string;
  path?: string;
  label?: string;
  origin?: string;
  duration?: string;
  validation?: string;
  owner_id?: string;
  labeler_id?: string;
  validator_id?: string;
  activity_type: "labeled" | "validated" | "recorded";
  stats?: UploadStats;
}

interface UploadHistoryItem {
  id: number;
  original_filename: string;
  display_name: string;
  category?: string;
  status: "in_progress" | "completed" | "error";
  created_at: string;
  updated_at: string;
  error_message?: string;
  stats?: UploadStats;
}

interface UploadHistoryMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

type PaginatedMeta = UploadHistoryMeta

type PaletteKey = "primary" | "success" | "warning" | "error"

const chipBaseStyles = {
  borderRadius: 9999,
  height: 32,
  fontWeight: 700,
  letterSpacing: 0.3,
  borderWidth: 1.5,
  '& .MuiChip-label': {
    paddingLeft: 9,
    paddingRight: 9,
    display: 'flex',
    alignItems: 'center',
    lineHeight: 1.2,
  },
} as const

export default function MyLabelsPage() {
  const { data: session, status } = useSession()
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const fileAccessBase =
    process.env.NEXT_PUBLIC_FILE_ACCESS_DOMAIN_LOCAL ||
    process.env.NEXT_PUBLIC_FILE_ACCESS_DOMAIN ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  const [stats, setStats] = useState({
    recorded_count: 0,
    labeled_count: 0,
    validated_count: 0,
    hours_recorded: 0,
    hours_labeled: 0,
    hours_validated: 0
  })
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [activityPage, setActivityPage] = useState(0)
  const [activityRowsPerPage, setActivityRowsPerPage] = useState(10)
  const [activityMeta, setActivityMeta] = useState<PaginatedMeta>({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 0
  })
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadForm, setUploadForm] = useState({
  name: "",
  category: "",
  consent: true
  })
  const [uploadFeedback, setUploadFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadPage, setUploadPage] = useState(0)
  const [uploadRowsPerPage, setUploadRowsPerPage] = useState(10)
  const [uploadMeta, setUploadMeta] = useState<UploadHistoryMeta>({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 0
  })

  const getStatsSnapshot = (stats?: UploadStats): UploadStats => ({
    total_generated: stats?.total_generated ?? 0,
    validated_count: stats?.validated_count ?? 0,
    labeled_count: stats?.labeled_count ?? 0,
    unlabeled_count: stats?.unlabeled_count ?? 0
  })

  const fetchUploads = useCallback(async (
    token: string,
    pageOverride?: number,
    pageSizeOverride?: number
  ) => {
    const page = pageOverride ?? uploadPage
    const pageSize = pageSizeOverride ?? uploadRowsPerPage
    try {
      const uploadsRes = await axios.get(`${apiBase}/uploads/history`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: page + 1,
          page_size: pageSize
        }
      })

      const payload = uploadsRes.data?.data
      if (payload?.items) {
        const items = Array.isArray(payload.items) ? payload.items : []
        setUploads(items)
        setUploadMeta(
          payload.meta ?? {
            page: page + 1,
            page_size: pageSize,
            total: items.length,
            total_pages: 1
          }
        )
      } else {
        const fallbackItems = Array.isArray(uploadsRes.data) ? uploadsRes.data : []
        setUploads(fallbackItems)
        setUploadMeta({
          page: page + 1,
          page_size: pageSize,
          total: fallbackItems.length,
          total_pages: 1
        })
      }
    } catch (error) {
      console.error("Failed to fetch uploads", error)
    }
  }, [apiBase, uploadPage, uploadRowsPerPage])

  const fetchActivity = useCallback(async (
    token: string,
    pageOverride?: number,
    pageSizeOverride?: number
  ) => {
    const page = pageOverride ?? activityPage
    const pageSize = pageSizeOverride ?? activityRowsPerPage
    try {
      const activityRes = await axios.get(`${apiBase}/users/activity`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: page + 1,
          page_size: pageSize
        }
      })

      const payload = activityRes.data?.data
      if (payload?.items) {
        const items = Array.isArray(payload.items) ? payload.items : []
        setActivity(items)
        setActivityMeta(
          payload.meta ?? {
            page: page + 1,
            page_size: pageSize,
            total: items.length,
            total_pages: 1
          }
        )
      } else {
        const fallbackItems = Array.isArray(activityRes.data) ? activityRes.data : []
        setActivity(fallbackItems)
        setActivityMeta({
          page: page + 1,
          page_size: pageSize,
          total: fallbackItems.length,
          total_pages: 1
        })
      }
    } catch (error) {
      console.error("Failed to fetch activity", error)
    }
  }, [apiBase, activityPage, activityRowsPerPage])

  useEffect(() => {
    if (!session?.user) return
    const token = (session as { accessToken?: string }).accessToken
    if (!token) return

    const fetchOverview = async () => {
      try {
        const statsRes = await axios.get(`${apiBase}/users/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const payload = statsRes.data || {}
        setStats({
          recorded_count: payload.recorded_count ?? 0,
          labeled_count: payload.labeled_count ?? 0,
          validated_count: payload.validated_count ?? 0,
          hours_recorded: payload.hours_recorded ?? 0,
          hours_labeled: payload.hours_labeled ?? 0,
          hours_validated: payload.hours_validated ?? 0
        })
      } catch (error) {
        console.error(error)
      }
    }

    fetchOverview()
  }, [session, apiBase])

  useEffect(() => {
    if (!session?.user) return
    const token = (session as { accessToken?: string }).accessToken
    if (!token) return
    fetchUploads(token, uploadPage, uploadRowsPerPage)
  }, [session, uploadPage, uploadRowsPerPage, fetchUploads])

  useEffect(() => {
    if (!session?.user) return
    const token = (session as { accessToken?: string }).accessToken
    if (!token) return
    fetchActivity(token, activityPage, activityRowsPerPage)
  }, [session, activityPage, activityRowsPerPage, fetchActivity])

  if (status === "loading") {
    return (
      <>
        <Container sx={{ mt: 10, textAlign: 'center' }}>
          <CircularProgress sx={{ mb: 3 }} />
          <Typography variant="h6" color="textSecondary">Loading your dashboard...</Typography>
        </Container>
        <Footer />
      </>
    )
  }

  if (status === "unauthenticated" || !session) {
    return (
      <>
        <Container sx={{ mt: 10, textAlign: 'center' }}>
          <Typography variant="h5" color="textSecondary">Please log in to view your labels.</Typography>
        </Container>
        <Footer />
      </>
    )
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0])
    }
  }

  const handleActivityPageChange = (_event: unknown, newPage: number) => {
    setActivityPage(newPage)
  }

  const handleActivityRowsPerPageChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setActivityRowsPerPage(parseInt(event.target.value, 10))
    setActivityPage(0)
  }

  const handleUploadPageChange = (_event: unknown, newPage: number) => {
    setUploadPage(newPage)
  }

  const handleUploadRowsPerPageChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setUploadRowsPerPage(parseInt(event.target.value, 10))
    setUploadPage(0)
  }

  const formatDuration = (value?: string | number | null) => {
    if (value === undefined || value === null) return '—'
    const numericValue = typeof value === 'string' ? parseFloat(value) : value
    if (Number.isNaN(numericValue)) {
      return value
    }
    return numericValue.toFixed(2)
  }

  const refreshUploads = async (token: string) => {
    await fetchUploads(token, 0, uploadRowsPerPage)
    setUploadPage(0)
  }

  const handleUploadSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setUploadFeedback(null)

    if (!selectedFile) {
      setUploadFeedback({ type: "error", message: "Please choose a file before uploading." })
      return
    }

    if (!uploadForm.consent) {
      setUploadFeedback({ type: "error", message: "Consent is required to upload media." })
      return
    }

    try {
      setIsUploading(true)
      const token = (session as { accessToken?: string }).accessToken
      if (!token) {
        setUploadFeedback({ type: "error", message: "You must be signed in to upload." })
        return
      }

      const formData = new FormData()
      formData.append("video_name", uploadForm.name || selectedFile.name.replace(/\.[^/.]+$/, ""))
      formData.append("video_category", uploadForm.category || "General")
      formData.append("consent", uploadForm.consent ? "true" : "false")
      formData.append("video_file", selectedFile)

      await axios.post(`${apiBase}/video/add`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      })

      setUploadFeedback({ type: "success", message: "Upload queued successfully. Processing has started." })
      setUploadForm({ name: "", category: "", consent: true })
      setSelectedFile(null)
      await refreshUploads(token)
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.response?.data?.message || "Upload failed."
        : "Upload failed."
      setUploadFeedback({ type: "error", message })
    } finally {
      setIsUploading(false)
    }
  }

  const renderStatusChip = (status: UploadHistoryItem["status"]) => {
    const statusConfig: Record<UploadHistoryItem["status"], { label: string; palette: PaletteKey }> = {
      completed: { label: "Completed", palette: "success" },
      in_progress: { label: "Processing", palette: "warning" },
      error: { label: "Error", palette: "error" }
    }

    const config = statusConfig[status]
    return (
      <Chip
        label={config.label}
        size="small"
        variant="outlined"
        sx={(theme) => ({
          ...chipBaseStyles,
          borderColor: theme.palette[config.palette].main,
          color: theme.palette[config.palette].main,
          backgroundColor: alpha(theme.palette[config.palette].main, 0.08),
        })}
      />
    )
  }

  const renderActivityChip = (activityType: ActivityItem["activity_type"]) => {
    const config: Record<ActivityItem["activity_type"], { label: string; palette: PaletteKey }> = {
      labeled: { label: "Labeled", palette: "primary" },
      validated: { label: "Validated", palette: "success" },
      recorded: { label: "Recorded", palette: "warning" }
    }

    const selected = config[activityType]
    return (
      <Chip
        label={selected.label}
        size="small"
        variant="outlined"
        sx={(theme) => ({
          ...chipBaseStyles,
          borderColor: theme.palette[selected.palette].main,
          color: theme.palette[selected.palette].main,
          backgroundColor: alpha(theme.palette[selected.palette].main, 0.08),
        })}
      />
    )
  }

  const StatCard = ({ title, value, icon, color }: { title: string, value: string | number, icon: ReactNode, color: string }) => (
    <Card elevation={0} sx={{ height: '100%', borderRadius: 4, border: '1px solid', borderColor: 'divider', transition: 'transform 0.2s', '&:hover': { transform: 'translateY(-4px)', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)' } }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', p: 3 }}>
            <Box sx={{ p: 2, borderRadius: 3, bgcolor: `${color}15`, color: color, mr: 2 }}>
                {icon}
            </Box>
            <Box>
                <Typography variant="body2" color="textSecondary" fontWeight={600} sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {title}
                </Typography>
                <Typography variant="h4" fontWeight={700} color="textPrimary">
                    {value}
                </Typography>
            </Box>
        </CardContent>
    </Card>
  )

  return (
    <>
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Box sx={{ mb: 6 }}>
          <Typography variant="h3" fontWeight={800} gutterBottom sx={{ background: 'linear-gradient(45deg, #A64D4A 30%, #FF8E53 90%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            My Dashboard
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Track your contributions and activity history
          </Typography>
      </Box>

      <Typography variant="h5" fontWeight={700} gutterBottom sx={{ mb: 3 }}>
        Key Insights
      </Typography>

        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard title="Recorded" value={stats.recorded_count} icon={<Mic size={28} />} color="#A64D4A" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard title="Labeled" value={stats.labeled_count} icon={<Edit3 size={28} />} color="#F97316" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard title="Validated" value={stats.validated_count} icon={<CheckCircle size={28} />} color="#10B981" />
          </Grid>
        </Grid>

        <Grid container spacing={3} sx={{ mb: 6 }}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard
              title="Hours Recorded"
              value={stats.hours_recorded.toFixed(2)}
              icon={<Timer size={28} />}
              color="#EF4444"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard
              title="Hours Labeled"
              value={stats.hours_labeled.toFixed(2)}
              icon={<Clock size={28} />}
              color="#3B82F6"
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <StatCard
              title="Hours Validated"
              value={stats.hours_validated.toFixed(2)}
              icon={<Activity size={28} />}
              color="#8B5CF6"
            />
          </Grid>
        </Grid>

      <Typography variant="h5" fontWeight={700} gutterBottom sx={{ mb: 3 }}>
        Recent Activity
      </Typography>
      <Paper elevation={0} sx={{ width: '100%', overflow: 'hidden', borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Index</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Audio</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Label</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Activity</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Duration (s)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activity.length > 0 ? activity.map((row, index) => (
                  <TableRow key={`${row.activity_type}-${row.id}`} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                      <TableCell>{activityPage * activityRowsPerPage + index + 1}</TableCell>
                      <TableCell sx={{ width: { xs: '100%', md: 280 } }}>
                        {row.path ? (
                          <Box sx={{
                            bgcolor: 'background.paper',
                            borderRadius: 2,
                            border: '1px solid',
                            borderColor: 'divider',
                            px: 1.5,
                            py: 1,
                          }}>
                            <audio
                              controls
                              src={buildFileAccessUrl(fileAccessBase, row.path)}
                              style={{ width: '100%', height: 32, background: 'transparent' }}
                            />
                          </Box>
                        ) : (
                          <Typography variant="body2" color="textSecondary">Clip unavailable</Typography>
                        )}
                      </TableCell>
                      <TableCell sx={{ width: { xs: '100%', md: '40%' } }}>
                        <Box
                          sx={{
                            fontFamily: 'monospace',
                            bgcolor: 'grey.50',
                            p: 1.5,
                            borderRadius: 2,
                            maxHeight: 140,
                            overflowY: 'auto',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                          }}
                        >
                          {row.label || '—'}
                        </Box>
                      </TableCell>
                      <TableCell>{renderActivityChip(row.activity_type)}</TableCell>
                      <TableCell>{formatDuration(row.duration)}</TableCell>
                  </TableRow>
                    )) : (
                  <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                          <Typography color="textSecondary">No activity found yet. Start labeling or recording!</Typography>
                      </TableCell>
                  </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
          <TablePagination
            component="div"
            count={activityMeta.total}
            page={activityPage}
            onPageChange={handleActivityPageChange}
            rowsPerPage={activityRowsPerPage}
            onRowsPerPageChange={handleActivityRowsPerPageChange}
            rowsPerPageOptions={[5, 10, 25, 50]}
          />
      </Paper>

      <Typography variant="h5" fontWeight={700} gutterBottom sx={{ mt: 6, mb: 3 }}>
        Uploaded Media
      </Typography>

      <Paper elevation={0} sx={{ mb: 4, borderRadius: 4, border: '1px solid', borderColor: 'divider', p: 4 }}>
        <Typography variant="h6" fontWeight={700} gutterBottom>
          Upload New Audio or Video
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Files are queued instantly and processed in the background. You can monitor their status below.
        </Typography>
        <Box component="form" onSubmit={handleUploadSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Title"
                placeholder="e.g., Dibra Interview"
                value={uploadForm.name}
                onChange={(e) => setUploadForm(prev => ({ ...prev, name: e.target.value }))}
                InputProps={{ sx: { borderRadius: 2 } }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label="Category"
                placeholder="Story, Conversation, ..."
                value={uploadForm.category}
                onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                InputProps={{ sx: { borderRadius: 2 } }}
              />
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Button
              component="label"
              variant="outlined"
              sx={{ borderRadius: 2 }}
            >
              Choose File
              <input type="file" hidden accept=".mp3,.mp4" onChange={handleFileChange} />
            </Button>
            {selectedFile ? (
              <Typography variant="body2" color="textSecondary">
                {selectedFile.name}
              </Typography>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Accepted formats: MP3, MP4
              </Typography>
            )}
          </Box>

          <FormControlLabel
            control={<Checkbox checked={uploadForm.consent} onChange={(e) => setUploadForm(prev => ({ ...prev, consent: e.target.checked }))} />}
            label={
              <Typography variant="body2" color="textSecondary">
                I agree to the{' '}
                <Link href="/termsandservices" className="text-primary font-semibold hover:underline">
                  Terms &amp; Conditions
                </Link>
                , including ownership and processing of my audio/video.
              </Typography>
            }
          />

          {uploadFeedback && (
            <Alert severity={uploadFeedback.type} sx={{ borderRadius: 2 }}>
              {uploadFeedback.message}
            </Alert>
          )}

          <Button
            type="submit"
            variant="contained"
            disabled={isUploading || !selectedFile}
            sx={{ alignSelf: 'flex-start', borderRadius: 2, px: 4, py: 1.5, fontWeight: 700 }}
          >
            {isUploading ? "Uploading..." : "Upload & Queue"}
          </Button>
        </Box>
      </Paper>

      <Paper elevation={0} sx={{ width: '100%', overflow: 'hidden', borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader aria-label="uploads table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Index</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Title</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>File Name</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Category</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Updated</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Generated</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Validated</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Labeled</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Unlabeled</TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {uploads.length > 0 ? uploads.map((row, index) => {
                const statsSnapshot = getStatsSnapshot(row.stats)
                return (
                <TableRow key={row.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                  <TableCell>{uploadPage * uploadRowsPerPage + index + 1}</TableCell>
                  <TableCell>{row.display_name}</TableCell>
                  <TableCell>{row.original_filename}</TableCell>
                  <TableCell>{row.category || '—'}</TableCell>
                  <TableCell>{renderStatusChip(row.status)}</TableCell>
                  <TableCell>{new Date(row.updated_at || row.created_at).toLocaleString()}</TableCell>
                  <TableCell>{statsSnapshot.total_generated}</TableCell>
                  <TableCell>{statsSnapshot.validated_count}</TableCell>
                  <TableCell>{statsSnapshot.labeled_count}</TableCell>
                  <TableCell>{statsSnapshot.unlabeled_count}</TableCell>
                  <TableCell>
                    {row.error_message ? (
                      <Typography variant="body2" color="error.main">
                        {row.error_message}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="textSecondary">
                        {row.status === "completed" ? "Ready for labeling" : "Queued"}
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              )}) : (
                <TableRow>
                  <TableCell colSpan={11} align="center" sx={{ py: 8 }}>
                    <Typography color="textSecondary">No uploads yet. Submit your first clip above.</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={uploadMeta.total}
          page={uploadPage}
          onPageChange={handleUploadPageChange}
          rowsPerPage={uploadRowsPerPage}
          onRowsPerPageChange={handleUploadRowsPerPageChange}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Paper>
    </Container>
    <Footer />
    </>
  )
}
