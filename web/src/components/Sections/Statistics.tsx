"use client";
import React, { useState, useEffect } from "react";
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Card, CardContent, Typography, Grid, Box } from "@mui/material";
import { styled } from '@mui/material/styles';
import axios from "axios";

const Root = styled(Box)(({ theme }) => ({
  padding: '60px 0',
  backgroundColor: 'var(--muted)',
  color: 'var(--foreground)',
}));

const StyledCard = styled(Card)(({ theme }) => ({
  boxShadow: '0px 5px 15px rgba(0, 0, 0, 0.1)',
  borderRadius: '15px',
  backgroundColor: 'var(--card)',
}));

const CircularProgressbarWrapper = styled('div')({
  height: '150px !important',
  width: '150px !important',
  marginBottom: '20px'
});

const Title = styled(Typography)({
  fontSize: '36px',
  fontWeight: 'bold',
  marginBottom: '20px',
  color: 'var(--primary)',
});

const SubTitle = styled(Typography)({
  fontStyle: 'italic',
  marginBottom: '30px'
});

const Paragraph = styled(Typography)({
  textAlign: 'justify',
  marginBottom: '30px'
});

const Label = styled(Typography)({
  fontSize: '18px',
  fontWeight: '500'
});

interface SummaryInfo {
  total_labeled: number;
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
  const [summaryInfo, setSummaryInfo] = useState<SummaryInfo | null>(null);

  useEffect(() => {
    async function fetchSummaryInfo() {
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL}dataset_insight_info`);
        const datas = response.data.data;
        if (!datas) return;
        const total = datas.total_labeled + datas.total_unlabeled;
        datas.sumofLabeled = (datas.total_labeled / total) * 100;
        datas.sumofUnLabeled = (datas.total_unlabeled / total) * 100;
        const totalDuration = datas.total_duration_labeled + datas.total_duration_unlabeled;
        datas.sumofLabeledDuration = (datas.total_duration_labeled / totalDuration) * 100;
        datas.sumofUnLabeledDuration = (datas.total_duration_unlabeled / totalDuration) * 100;
        datas.progressPercentage = (datas.total_duration_validated / totalDuration) * 100;

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

  return (
    <Root>
      <div className="container mx-auto px-4">
        <Grid container justifyContent="center">
          <Grid size={{ xs: 12, sm: 10, md: 8 }}>
            <Title variant="h2" sx={{ display: 'inline-block', padding: 0 }}>THE PROJECT</Title>
            <SubTitle variant="h5">We love Technology</SubTitle>
            <Paragraph variant="body1">
              Welcome to the Albanian Language Transcriber project! Our goal is to develop a functioning Albanian speech-to-text AI model to improve the lives
              of Albanians and promote the development of the country. With over 7 million speakers, the Albanian language is an important language with a rich
              cultural heritage, yet it currently lacks a speech-to-text tool. By developing this tool, we aim to bring the benefits of speech recognition
              technology to Albanian speakers in various fields, including the smartphone, automobile, medical, education, and jurisdiction industries. Our team
              is committed to building a high-quality model that achieves an accuracy rate of 80% and makes a meaningful impact on the Albanian community. We
              appreciate your support and interest in our project.
            </Paragraph>
            <Title variant="h2">OUR DATASET SO FAR LOCAL</Title>
            {summaryInfo && (
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <StyledCard>
                    <CardContent sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgressbarWrapper>
                        <CircularProgressbar
                          value={summaryInfo.sumofLabeled}
                          text={`${summaryInfo.sumofLabeled.toFixed(2)}%`}
                          styles={buildStyles({
                            pathColor: 'var(--primary)',
                            textColor: 'var(--foreground)',
                            trailColor: 'var(--muted)',
                          })}
                        />
                      </CircularProgressbarWrapper>
                      <Label>Labeled Data</Label>
                    </CardContent>
                  </StyledCard>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <StyledCard>
                    <CardContent sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgressbarWrapper>
                        <CircularProgressbar
                          value={summaryInfo.sumofUnLabeled}
                          text={`${summaryInfo.sumofUnLabeled.toFixed(2)}%`}
                          styles={buildStyles({
                            pathColor: 'var(--primary)',
                            textColor: 'var(--foreground)',
                            trailColor: 'var(--muted)',
                          })}
                        />
                      </CircularProgressbarWrapper>
                      <Label>Unlabeled Data</Label>
                    </CardContent>
                  </StyledCard>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <StyledCard>
                    <CardContent sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgressbarWrapper>
                        <CircularProgressbar
                          value={summaryInfo.sumofLabeledDuration}
                          text={`${summaryInfo.sumofLabeledDuration.toFixed(2)}%`}
                          styles={buildStyles({
                            pathColor: 'var(--primary)',
                            textColor: 'var(--foreground)',
                            trailColor: 'var(--muted)',
                          })}
                        />
                      </CircularProgressbarWrapper>
                      <Label>Labeled Data Duration</Label>
                    </CardContent>
                  </StyledCard>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <StyledCard>
                    <CardContent sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgressbarWrapper>
                        <CircularProgressbar
                          value={summaryInfo.sumofUnLabeledDuration}
                          text={`${summaryInfo.sumofUnLabeledDuration.toFixed(2)}%`}
                          styles={buildStyles({
                            pathColor: 'var(--primary)',
                            textColor: 'var(--foreground)',
                            trailColor: 'var(--muted)',
                          })}
                        />
                      </CircularProgressbarWrapper>
                      <Label>Unlabeled Data Duration</Label>
                    </CardContent>
                  </StyledCard>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <StyledCard>
                    <CardContent sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <CircularProgressbarWrapper>
                        <CircularProgressbar
                          value={summaryInfo.progressPercentage}
                          text={`${summaryInfo.progressPercentage.toFixed(2)}%`}
                          styles={buildStyles({
                            pathColor: 'var(--primary)',
                            textColor: 'var(--foreground)',
                            trailColor: 'var(--muted)',
                          })}
                        />
                      </CircularProgressbarWrapper>
                      <Label>Validated Data</Label>
                    </CardContent>
                  </StyledCard>
                </Grid>
              </Grid>
            )}
          </Grid>
        </Grid>
      </div>
    </Root>
  );
}
