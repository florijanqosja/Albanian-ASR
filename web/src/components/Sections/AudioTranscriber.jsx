import React from "react";
import RecorderControls from "../recorder-controls";
import RecordingsList from "../recordings-list";
import useRecorder from "../../hooks/useRecorder";
import styled from "styled-components";
import Button from "@material-ui/core/Button";
import axios from "axios";

export default function MainSection() {
  const { recorderState, ...handlers } = useRecorder();
  const { audio } = recorderState;

  const handleSubmit = async () => {
    // try {
    //   await axios.put(`${process.env.REACT_APP_API_DOMAIN}audio/validate`, {
    //     Sp_ID: audioID,
    //     Sp_LABEL: labelValue,
    //   });
    // } catch (error) {
    //   console.error("Failed to perform PUT request:", error);
    // }
    console.log("PUT request successful");
  };
  
  return (
    <VoiceRecorder>
      <RecorderContainer>
        <Title>Record your voice</Title>
        <RecorderControls recorderState={recorderState} handlers={handlers} />
        <RecordingsList audio={audio} />
      </RecorderContainer>
    </VoiceRecorder>
  );
};

const VoiceRecorder = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 500px;
  margin-top: 80px;
`;

const RecorderContainer = styled.div`
  width: 800px;
  background-color: #cda5a3;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-around; // Distribute space between items
  align-items: center;
`;

const Title = styled.h2`
  font-size: 36px;
  font-weight: bold;
  color: #301616;
`;
