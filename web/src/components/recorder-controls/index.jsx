import { FaMicrophone, FaTimes, FaSave } from "react-icons/fa";
import { formatMinutes, formatSeconds } from "../../utils/format-time";
import "./styles.css";

export default function RecorderControls({ recorderState, handlers }) {
  const { recordingMinutes, recordingSeconds, initRecording } = recorderState;
  const { startRecording, saveRecording, cancelRecording } = handlers;

  return (
    <div className="controls-container">
      <br />
      <br />
      <br />
      <br />
      <br />
      
      <div className="recorder-display">
        <div className="recording-time">
          {initRecording && <div className="recording-indicator"></div>}
          <span>{formatMinutes(recordingMinutes)}</span>
          <span>:</span>
          <span>{formatSeconds(recordingSeconds)}</span>
        </div>
        {initRecording && (
          <div className="cancel-button-container">
            <button className="cancel-button" title="Cancel recording" onClick={cancelRecording}>
              <FaTimes />
            </button>
          </div>
        )}
      </div>
      <div className="start-button-container">
        {initRecording ? (
          <button
            className="start-button"
            title="Save recording"
            disabled={recordingSeconds === 0}
            onClick={saveRecording}
          >
            <FaSave />
          </button>
        ) : (
          <button className="start-button" title="Start recording" onClick={startRecording}>
            <FaMicrophone />
          </button>
        )}
      </div>
    </div>
  );
}
