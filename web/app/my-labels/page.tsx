"use client"
import { useSession } from "next-auth/react"
import { useState, useEffect } from "react"
import { Container, Typography, Paper, Grid, Card, CardContent, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box, Chip } from "@mui/material"
import { CheckCircle, Mic, Clock, Activity } from "lucide-react"
import axios from "axios"
import Footer from "@/components/Sections/Footer"
import { buildFileAccessUrl } from "@/lib/utils"

interface ActivityItem {
    id: number;
    path: string;
    label: string;
    created_at?: string;
}

export default function MyLabelsPage() {
  const { data: session } = useSession()
  const [stats, setStats] = useState({
    labeled_count: 0,
    validated_count: 0,
    hours_labeled: 0,
    hours_validated: 0
  })
  const [activity, setActivity] = useState<ActivityItem[]>([])

  useEffect(() => {
    if (session?.user) {
        const fetchData = async () => {
            try {
                const token = (session as { accessToken?: string }).accessToken
                const statsRes = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/stats`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                setStats(statsRes.data)

                const activityRes = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/activity`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                setActivity(activityRes.data)
            } catch (e) {
                console.error(e)
            }
        }
        fetchData()
    }
  }, [session])

  if (!session) return (
    <Container sx={{ mt: 10, textAlign: 'center' }}>
        <Typography variant="h5" color="textSecondary">Please log in to view your labels.</Typography>
    </Container>
  )

  const StatCard = ({ title, value, icon, color }: { title: string, value: string | number, icon: React.ReactNode, color: string }) => (
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
      
      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard title="Labeled" value={stats.labeled_count} icon={<Mic size={28} />} color="#A64D4A" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard title="Validated" value={stats.validated_count} icon={<CheckCircle size={28} />} color="#10B981" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard title="Hours Labeled" value={stats.hours_labeled} icon={<Clock size={28} />} color="#3B82F6" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard title="Hours Validated" value={stats.hours_validated} icon={<Activity size={28} />} color="#8B5CF6" />
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
                <TableCell sx={{ fontWeight: 700, bgcolor: 'background.paper' }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activity.length > 0 ? activity.map((row, index) => (
                  <TableRow key={row.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                          <audio
                            controls
                            src={buildFileAccessUrl(process.env.NEXT_PUBLIC_FILE_ACCESS_DOMAIN_LOCAL || "http://localhost:8000", row.path)}
                            style={{ height: 32, borderRadius: 20 }}
                          />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'grey.50', p: 1, borderRadius: 1 }}>
                            {row.label && row.label.length > 80 ? row.label.substring(0, 80) + "..." : row.label}
                        </Typography>
                      </TableCell>
                      <TableCell>
                          <Chip label="Completed" size="small" color="success" variant="outlined" />
                      </TableCell>
                  </TableRow>
              )) : (
                  <TableRow>
                      <TableCell colSpan={4} align="center" sx={{ py: 8 }}>
                          <Typography color="textSecondary">No activity found yet. Start labeling!</Typography>
                      </TableCell>
                  </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
    <Footer />
    </>
  )
}
