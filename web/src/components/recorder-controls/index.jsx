import { FaMicrophone, FaTimes, FaSave } from "react-icons/fa";
import { formatMinutes, formatSeconds } from "../../utils/format-time";
import styled from 'styled-components';

export default function RecorderControls({ recorderState, handlers }) {
  const { recordingMinutes, recordingSeconds, initRecording } = recorderState;
  const { startRecording, saveRecording, cancelRecording } = handlers;

  return (
    <ControlsContainer>
      <RecorderDisplay>
        <RecordingTime>
          {initRecording && <RecordingIndicator />}
          <span>{formatMinutes(recordingMinutes)}</span>
          <span>:</span>
          <span>{formatSeconds(recordingSeconds)}</span>
        </RecordingTime>
        {initRecording && (
          <CancelButtonContainer>
            <IconButton title="Cancel recording" onClick={cancelRecording}>
              <FaTimes />
            </IconButton>
          </CancelButtonContainer>
        )}
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
`;

const RecorderDisplay = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
`;

const RecordingTime = styled.div`
  display: flex;
  align-items: center;
`;

const RecordingIndicator = styled.div`
  height: 10px;
  width: 10px;
  background-color: red;
  border-radius: 50%;
  margin-right: 5px;
`;

const CancelButtonContainer = styled.div`
  margin-left: auto;
`;

const StartButtonContainer = styled.div`
  display: flex;
  justify-content: center;
  width: 100%;
`;

const IconButton = styled.button`
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
`;
