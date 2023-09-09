import React from "react";
import RecorderControls from "../recorder-controls";
import RecordingsList from "../recordings-list";
import useRecorder from "../../hooks/useRecorder";
import styled from "styled-components";

export default function MainSection() {
  const { recorderState, ...handlers } = useRecorder();
  const { audio } = recorderState;
  
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
  height: 450px; // Fixed height
  background: linear-gradient(135deg, #f5e6e8, #cda5a3); // Gradient background for a modern touch
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between; // Distribute space between items
  align-items: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); // Subtle shadow for depth
  transition: transform 0.2s ease, box-shadow 0.2s ease; // Smooth transition for hover effect
`;


const Title = styled.h2`
  font-size: 36px;
  font-weight: bold;
  color: #301616;
`;
