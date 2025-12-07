"use client";
import React, { useState, useEffect } from "react";
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Typography, Grid, Box, Container, Paper } from "@mui/material";
import { Database, CheckCircle, Clock, ClipboardCheck } from "lucide-react";
import axios from "axios";
import { useTranslations } from "next-intl";

interface SummaryInfo {
  total_labeled: number;
  total_validated: number;
  total_unlabeled: number;
  sumofLabeled: number;
  sumofUnLabeled: number;
  total_duration_labeled: number;
  total_duration_unlabeled: number;
  total_duration_validated: number;
  sumofLabeledDuration: number;
  sumofUnLabeledDuration: number;
  progressPercentage: number;
}

export default function Statistics() {
    const t = useTranslations("stats");
  const [summaryInfo, setSummaryInfo] = useState<SummaryInfo | null>(null);

  useEffect(() => {
    async function fetchSummaryInfo() {
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL || 'http://localhost:8000/'}dataset_insight_info`);
        const datas = response.data.data;
        if (!datas) return;
                const total = (datas.total_labeled || 0) + (datas.total_unlabeled || 0);
                if (total > 0) {
                    datas.sumofLabeled = (datas.total_labeled / total) * 100;
                    datas.sumofUnLabeled = (datas.total_unlabeled / total) * 100;
                } else {
                    datas.sumofLabeled = 0;
                    datas.sumofUnLabeled = 0;
                }

                const totalDuration = (datas.total_duration_labeled || 0) + (datas.total_duration_unlabeled || 0);
                if (totalDuration > 0) {
                    datas.sumofLabeledDuration = (datas.total_duration_labeled / totalDuration) * 100;
                    datas.sumofUnLabeledDuration = (datas.total_duration_unlabeled / totalDuration) * 100;
                    datas.progressPercentage = (datas.total_duration_validated / totalDuration) * 100;
                } else {
                    datas.sumofLabeledDuration = 0;
                    datas.sumofUnLabeledDuration = 0;
                    datas.progressPercentage = 0;
                }

        // Convert seconds to hours
        datas.total_duration_labeled /= 3600;
        datas.total_duration_unlabeled /= 3600;
        datas.total_duration_validated /= 3600;

        setSummaryInfo(datas);
      } catch (error) {
        console.error("Error fetching summary info:", error);
      }
    }

    fetchSummaryInfo();
  }, []);

    const StatCard = ({ title, value, subtitle, icon, color }: { title: string, value: string | number, subtitle: string, icon: React.ReactNode, color: string }) => (
    <Paper elevation={0} sx={{ p: 3, height: '100%', borderRadius: 4, border: '1px solid', borderColor: 'divider', transition: 'all 0.3s', '&:hover': { transform: 'translateY(-5px)', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)' } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: `${color}15`, color: color, mr: 2 }}>
                {icon}
            </Box>
            <Typography variant="h6" fontWeight={700} color="textPrimary">
                {title}
            </Typography>
        </Box>
        <Typography variant="h3" fontWeight={800} sx={{ mb: 1, background: `linear-gradient(45deg, ${color}, ${color}dd)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            {value}
        </Typography>
        <Typography variant="body2" color="textSecondary">
            {subtitle}
        </Typography>
    </Paper>
  );

  return (
    <Box sx={{ py: 10, bgcolor: 'grey.50' }}>
      <Container maxWidth="lg">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="overline" color="primary" fontWeight={700} letterSpacing={2}>
                {t("eyebrow")}
            </Typography>
            <Typography variant="h2" fontWeight={800} sx={{ mt: 1, mb: 3, background: 'linear-gradient(45deg, #1F2937 30%, #4B5563 90%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {t("title")}
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ maxWidth: 700, mx: 'auto', fontSize: '1.1rem', lineHeight: 1.8 }}>
                {t("body")}
            </Typography>
        </Box>

        {summaryInfo && (
            <Grid container spacing={4}>
                <Grid size={{ xs: 12, md: 4 }}>
                    <Box sx={{ textAlign: 'center', p: 4, bgcolor: 'white', borderRadius: 4, height: '100%', border: '1px solid', borderColor: 'divider' }}>
                        <Typography variant="h6" fontWeight={700} gutterBottom>{t("progress")}</Typography>
                        <Box sx={{ width: 180, height: 180, mx: 'auto', my: 4 }}>
                            <CircularProgressbar
                                value={summaryInfo.progressPercentage}
                                text={`${summaryInfo.progressPercentage.toFixed(1)}%`}
                                styles={buildStyles({
                                    pathColor: `#A64D4A`,
                                    textColor: '#1F2937',
                                    trailColor: '#F3F4F6',
                                    textSize: '16px',
                                })}
                            />
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                            {t("progressHelp")}
                        </Typography>
                    </Box>
                </Grid>
                
                <Grid size={{ xs: 12, md: 8 }}>
                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, sm: 6 }}>
                            <StatCard 
                                title={t("totalLabeled")} 
                                value={summaryInfo.total_labeled.toLocaleString()} 
                                subtitle={t("labeledSubtitle", { percent: summaryInfo.sumofLabeled.toFixed(1) })}
                                icon={<Database size={24} />}
                                color="#3B82F6"
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6 }}>
                            <StatCard 
                                title={t("validatedHours")}
                                value={summaryInfo.total_duration_validated.toFixed(1)} 
                                subtitle={t("validatedHoursSubtitle")}
                                icon={<CheckCircle size={24} />}
                                color="#10B981"
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6 }}>
                            <StatCard 
                                title={t("labeledHours")}
                                value={summaryInfo.total_duration_labeled.toFixed(1)} 
                                subtitle={t("labeledHoursSubtitle")}
                                icon={<Clock size={24} />}
                                color="#F59E0B"
                            />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 6 }}>
                            <StatCard 
                                title={t("totalValidated")}
                                value={summaryInfo.total_validated?.toLocaleString() || "0"} 
                                subtitle={t("totalValidatedSubtitle")}
                                icon={<ClipboardCheck size={24} />}
                                color="#8B5CF6"
                            />
                        </Grid>
                    </Grid>
                </Grid>
            </Grid>
        )}
      </Container>
    </Box>
  );
}
