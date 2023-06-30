import React, { useState, useEffect } from "react";
import styled from "styled-components";

const SectionWrapper = styled.div`
  background-color: #d8d4d4;
  padding: 60px 0;
`;

const ContentWrapper = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const SectionHeading = styled.h2`
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #301616;
`;

const SectionSubHeading = styled.p`
  font-style: italic;
  margin-bottom: 30px;
  color: #a99b9d;
`;

const SectionText = styled.p`
  text-align: justify;
  margin-bottom: 30px;
  color: #301616;
`;

const DataContainer = styled.div`
  margin-bottom: 30px;
`;

const DataLabel = styled.p`
  font-size: 18px;
  margin-bottom: 10px;
  color: #301616;
`;

const DataBar = styled.div`
  background-color: #e1dddd;
  height: 10px;
  border-radius: 5px;
`;

const DataProgress = styled.div`
  height: 100%;
  background-color: #9e3936;
  border-radius: 5px;
`;

export default function Pricing() {
  const [summaryInfo, setSummaryInfo] = useState(null);

  useEffect(() => {
    async function fetchSummaryInfo() {
      try {
        const response = await fetch("https://api.uneduashqiperine.com/dataset_insight_info/");
        const datas = await response.json();
        setSummaryInfo(datas);
      } catch (error) {
        console.error("Error fetching summary info:", error);
      }
    }

    fetchSummaryInfo();
  }, []);

  return (
    <SectionWrapper>
      <ContentWrapper>
        <SectionHeading>THE PROJECT</SectionHeading>
        <SectionSubHeading>We love Technology</SectionSubHeading>
        <SectionText>
          Welcome to the Albanian Language Transcriber project! Our goal is to develop a functioning Albanian speech-to-text AI model to improve the lives
          of Albanians and promote the development of the country. With over 7 million speakers, the Albanian language is an important language with a rich
          cultural heritage, yet it currently lacks a speech-to-text tool. By developing this tool, we aim to bring the benefits of speech recognition
          technology to Albanian speakers in various fields, including the smartphone, automobile, medical, education, and jurisdiction industries. Our team
          is committed to building a high-quality model that achieves an accuracy rate of 80% and makes a meaningful impact on the Albanian community. We
          appreciate your support and interest in our project.
        </SectionText>
        <SectionHeading>OUR DATASET SO FAR</SectionHeading>
        {summaryInfo && (
          <>
            <DataContainer>
              <DataLabel>Labeled Datas</DataLabel>
              <DataBar>
                <DataProgress style={{ width: `${summaryInfo.sumofLabeled}%` }} />
              </DataBar>
            </DataContainer>
            <DataContainer>
              <DataLabel>UnLabeled Datas</DataLabel>
              <DataBar>
                <DataProgress style={{ width: `${summaryInfo.sumofUnLabeled}%` }} />
              </DataBar>
            </DataContainer>
            <DataContainer>
              <DataLabel>Labeled Datas Duration</DataLabel>
              <DataBar>
                <DataProgress style={{ width: `${summaryInfo.sumofLabeledDuration}%` }} />
              </DataBar>
            </DataContainer>
            <DataContainer>
              <DataLabel>UnLabeled Datas Duration</DataLabel>
              <DataBar>
                <DataProgress style={{ width: `${summaryInfo.sumofUnLabeledDuration}%` }} />
              </DataBar>
            </DataContainer>
            <DataContainer>
              <DataLabel>Progress</DataLabel>
              <DataBar>
                <DataProgress style={{ width: `${summaryInfo.progressPercentage}` }} />
              </DataBar>
            </DataContainer>
          </>
        )}
      </ContentWrapper>
    </SectionWrapper>
  );
}
