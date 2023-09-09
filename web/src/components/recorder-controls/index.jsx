import { FaMicrophone, FaTimes, FaSave } from "react-icons/fa";
import { formatMinutes, formatSeconds } from "../../utils/format-time";
import styled, { keyframes } from 'styled-components';

export default function RecorderControls({ recorderState, handlers }) {
  const { recordingMinutes, recordingSeconds, initRecording } = recorderState;
  const { startRecording, saveRecording } = handlers;

  return (
    <ControlsContainer>
      <RecorderDisplay>
        <RecordingTime>
          <span>{formatMinutes(recordingMinutes)}</span>
          <span>:</span>
          <span>{formatSeconds(recordingSeconds)}</span>
        </RecordingTime>
      </RecorderDisplay>

      <StartButtonContainer>
        {initRecording ? (
          <IconButton
            title="Save recording"
            disabled={recordingSeconds === 0}
            onClick={saveRecording}
          >
            <FaSave />
          </IconButton>
        ) : (
          <IconButton title="Start recording" onClick={startRecording}>
            <FaMicrophone />
          </IconButton>
        )}
      </StartButtonContainer>
    </ControlsContainer>
  );
}

const ControlsContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
`;

const RecorderDisplay = styled.div`
  display: flex;
  align-items: center;
  justify-content: center; // This ensures the timer is centered
  width: 100%;
  margin-bottom: 1rem;
`;

const RecordingTime = styled.div`
  display: flex;
  align-items: center;
  font-size: 1.5rem; // Increased font size for better visibility
  color: #301616; // Dark color for better contrast
`;

const StartButtonContainer = styled.div`
  display: flex;
  justify-content: center;
  width: 100%;
`;

const colorPulse = keyframes`
  0% { color: #301616; }
  50% { color: #b33e3a; }
  100% { color: #301616; }
`;


const IconButton = styled.button`
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #301616;
  transition: transform 0.3s ease, color 0.3s ease;
  animation: ${props => props.recording ? `${colorPulse} 1s infinite` : 'none'}; // Apply animation if recording

  &:hover {
    transform: scale(1.1);
    color: #b33e3a; 
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
`;

