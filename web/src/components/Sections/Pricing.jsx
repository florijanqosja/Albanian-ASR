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
  validatedCard: {
    backgroundColor: '#90ee90', // light green for validated
  },
  labeledCard: {
    backgroundColor: '#ffff99', // light yellow for labeled
  },
  unlabeledCard: {
    backgroundColor: '#cda5a3', // same as is now for unlabeled
  },
}));

const secondsToHours = (seconds) => (seconds / 3600).toFixed(2);

export default function Pricing() {
  const classes = useStyles();
  const [summaryInfo, setSummaryInfo] = useState(null);

  useEffect(() => {
    async function fetchSummaryInfo() {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_DOMAIN_PROD}dataset_insight_info`);
        const data = response.data;
        const total = data.total_labeled + data.total_unlabeled + data.total_validated;
        const totalDuration = data.total_duration_labeled + data.total_duration_unlabeled + data.total_duration_validated;
        data.sumofLabeled = data.total_labeled;
        data.sumofUnLabeled = data.total_unlabeled;
        data.sumofValidated = data.total_validated;
        data.sumofLabeledDuration = data.total_duration_labeled;
        data.sumofUnLabeledDuration = data.total_duration_unlabeled;
        data.progressPercentage = data.total_duration_validated;
        setSummaryInfo(data);
      } catch (error) {
        console.error('Error fetching summary info:', error);
      }
    }
    fetchSummaryInfo();
  }, []);

  const calculatePercentage = (partialValue, totalValue) => {
    return ((100 * partialValue) / totalValue).toFixed(2);
  };

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
          <Typography variant="h2" className={classes.title}>OUR DATASET SO FAR Prod</Typography>
          {summaryInfo && (
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.unlabeledCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Unlabeled Data</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_unlabeled} / ${(summaryInfo.total_labeled + summaryInfo.total_unlabeled + summaryInfo.total_validated)} entries`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.unlabeledCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Unlabeled Data Duration</Typography>
                    <Typography variant="body2">{`${secondsToHours(summaryInfo.total_duration_unlabeled)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.labeledCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Labeled Data</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_labeled} / ${(summaryInfo.total_labeled + summaryInfo.total_unlabeled + summaryInfo.total_validated)} entries`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.labeledCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Labeled Data Duration</Typography>
                    <Typography variant="body2">{`${secondsToHours(summaryInfo.total_duration_labeled)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.validatedCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Validated Data</Typography>
                    <Typography variant="body2">{`${summaryInfo.total_validated} / ${(summaryInfo.total_labeled + summaryInfo.total_unlabeled + summaryInfo.total_validated)}`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.validatedCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>Validated Data Duration</Typography>
                    <Typography variant="body2">{`${secondsToHours(summaryInfo.total_duration_validated)} hours`}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.unlabeledCard}`}>
                  <CardContent align="center">
                  <Typography variant="h6" className={classes.label}>
                    Progress<br />
                    Unlabeled - Labeled
                  </Typography>
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={calculatePercentage(
                          summaryInfo.total_unlabeled,
                          (summaryInfo.total_labeled + summaryInfo.total_unlabeled))}
                        text={`${calculatePercentage(
                          summaryInfo.total_unlabeled,
                          (summaryInfo.total_labeled + summaryInfo.total_unlabeled))}%`}
                        styles={buildStyles({
                          strokeLinecap: 'butt',
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.labeledCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>
                      Progress<br />
                      Labeled - Validated</Typography>
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={calculatePercentage(
                          summaryInfo.total_labeled,
                          (summaryInfo.total_labeled + summaryInfo.total_validated))}
                        text={`${calculatePercentage(
                          summaryInfo.total_labeled,
                          (summaryInfo.total_labeled + summaryInfo.total_validated))}%`}
                        styles={buildStyles({
                          strokeLinecap: 'butt',
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Card className={`${classes.card} ${classes.validatedCard}`}>
                  <CardContent align="center">
                    <Typography variant="h6" className={classes.label}>
                      Progress<br />
                      Unlabeled - Validated</Typography>
                    <div className={classes.circularProgressbar}>
                      <CircularProgressbar
                        value={calculatePercentage(
                          (summaryInfo.total_unlabeled + summaryInfo.total_labeled),
                          (summaryInfo.total_labeled + summaryInfo.total_validated + summaryInfo.total_unlabeled))}
                        text={`${calculatePercentage(
                          (summaryInfo.total_unlabeled + summaryInfo.total_labeled),
                          (summaryInfo.total_labeled + summaryInfo.total_validated + summaryInfo.total_unlabeled))}%`}
                        styles={buildStyles({
                          strokeLinecap: 'butt',
                          textColor: '#301616',
                          pathColor: '#301616',
                          trailColor: '#d6d6d6',
                        })}
                      />
                    </div>
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