import React, { useState, useEffect } from "react";
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Card, CardContent, Typography, Grid, Box } from "@material-ui/core";
import { makeStyles } from '@material-ui/core/styles';
import axios from "axios";

const useStyles = makeStyles((theme) => ({
  root: {
    padding: '60px 0',
    backgroundColor: '#DFD5D5',
    color: '#301616',
  },
  card: {
    boxShadow: '0px 5px 15px rgba(0, 0, 0, 0.1)',
    borderRadius: '15px',
    backgroundColor: '#cda5a3',
  },
  circularProgressbar: {
    height: '150px !important',
    width: '150px !important',
    marginBottom: '20px'
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '20px'
  },
  subTitle: {
    fontStyle: 'italic',
    marginBottom: '30px'
  },
  paragraph: {
    textAlign: 'justify',
    marginBottom: '30px'
  },
  label: {
    fontSize: '18px',
    fontWeight: '500'
  },
}));


export default function Pricing() {
  const classes = useStyles();
  const [summaryInfo, setSummaryInfo] = useState(null);

  useEffect(() => {
    async function fetchSummaryInfo() {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_DOMAIN_PROD}dataset_insight_info`);
        const datas = response.data;
        const total = datas.total_labeled + datas.total_unlabeled;
        datas.sumofLabeled = (datas.total_labeled / total) * 100;
        datas.sumofUnLabeled = (datas.total_unlabeled / total) * 100;
        const totalDuration = datas.total_duration_labeled + datas.total_duration_unlabeled;
        datas.sumofLabeledDuration = (datas.total_duration_labeled / totalDuration) * 100;
        datas.sumofUnLabeledDuration = (datas.total_duration_unlabeled / totalDuration) * 100;
        datas.progressPercentage = (datas.total_duration_validated / totalDuration) * 100;
        setSummaryInfo(datas);
      } catch (error) {
        console.error("Error fetching summary info:", error);
      }
    }

    fetchSummaryInfo();
  }, []);

  return (
    <Box className={classes.root}>
      <Grid container justify="center">
        <Grid item xs={14} sm={8} md={7}>
          <Typography variant="h2" backgroundColor="#cda5a3" className={classes.title}>THE PROJECT</Typography>
          <Typography variant="h5" className={classes.subTitle}>We love Technology</Typography>
          <Typography variant="body1" className={classes.paragraph}>
            Welcome to the Albanian Language Transcriber project! Our goal is to develop a functioning Albanian speech-to-text AI model to improve the lives
            of Albanians and promote the development of the country. With over 7 million speakers, the Albanian language is an important language with a rich
            cultural heritage, yet it currently lacks a speech-to-text tool. By developing this tool, we aim to bring the benefits of speech recognition
            technology to Albanian speakers in various fields, including the smartphone, automobile, medical, education, and jurisdiction industries. Our team
            is committed to building a high-quality model that achieves an accuracy rate of 80% and makes a meaningful impact on the Albanian community. We
            appreciate your support and interest in our project.
          </Typography>
          <Typography variant="h2" className={classes.title}>OUR DATASET SO FAR</Typography>
          {summaryInfo && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={classes.card}>
                  <CardContent align="center">
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={summaryInfo.sumofLabeled}
                        text={`${summaryInfo.sumofLabeled.toFixed(2)}%`}
                        styles={buildStyles({
                          strokeLinecap: "butt",
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                    <Typography variant="h6" className={classes.label}>Labeled Data</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_labeled} / ${summaryInfo.total_labeled + summaryInfo.total_unlabeled}`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={classes.card}>
                  <CardContent align="center">
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={summaryInfo.sumofUnLabeled}
                        text={`${summaryInfo.sumofUnLabeled.toFixed(2)}%`}
                        styles={buildStyles({
                          strokeLinecap: "butt",
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                    <Typography variant="h6" className={classes.label}>Unlabeled Data</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_unlabeled} / ${summaryInfo.total_labeled + summaryInfo.total_unlabeled}`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={classes.card}>
                  <CardContent align="center">
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={summaryInfo.sumofLabeledDuration}
                        text={`${summaryInfo.sumofLabeledDuration.toFixed(2)}%`}
                        styles={buildStyles({
                          strokeLinecap: "butt",
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                    <Typography variant="h6" className={classes.label}>Labeled Data Duration</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_duration_labeled.toFixed(2)} / ${(summaryInfo.total_duration_labeled + summaryInfo.total_duration_unlabeled).toFixed(2)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={classes.card}>
                  <CardContent align="center">
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={summaryInfo.sumofUnLabeledDuration}
                        text={`${summaryInfo.sumofUnLabeledDuration.toFixed(2)}%`}
                        styles={buildStyles({
                          strokeLinecap: "butt",
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                    <Typography variant="h6" className={classes.label}>Unlabeled Data Duration</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_duration_unlabeled.toFixed(2)} / ${(summaryInfo.total_duration_labeled + summaryInfo.total_duration_unlabeled).toFixed(2)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={classes.card}>
                  <CardContent align="center">
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={summaryInfo.progressPercentage}
                        text={`${summaryInfo.progressPercentage.toFixed(2)}%`}
                        styles={buildStyles({
                          strokeLinecap: "butt",
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                    <Typography variant="h6" className={classes.label}>Progress</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_duration_validated.toFixed(2)} / ${(summaryInfo.total_duration_labeled + summaryInfo.total_duration_unlabeled).toFixed(2)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
