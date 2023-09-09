import { FaTrashAlt } from "react-icons/fa";
import useRecordingsList from "../../hooks/use-recordings-list";
import "./styles.css";
import Button from "@material-ui/core/Button";
import axios from "axios";
import { useState } from "react";

export default function RecordingsList({ audio }) {
  const { recordings, deleteAudio } = useRecordingsList(audio);
  const [transcriptions, setTranscriptions] = useState({});
  const [transcriptionStatus, setTranscriptionStatus] = useState({});

  const handleTranscription = async (audioBlobURL, key) => {
    setTranscriptionStatus(prev => ({ ...prev, [key]: 'transcribing' }));
    try {
        // Fetch the blob from the blob URL
        const responseBlob = await fetch(audioBlobURL);
        const audioBlob = await responseBlob.blob();

        const formData = new FormData();
        formData.append("file_wav", audioBlob, "audio.wav");

        const response = await axios.post("http://localhost:140/transcribe", formData);
        setTranscriptions(prev => ({ ...prev, [key]: response.data }));
        setTranscriptionStatus(prev => ({ ...prev, [key]: 'completed' }));
    } catch (err) {
        console.error("Error:", err);
    }
  };

  return (
    <div className="recordings-container">
      {recordings.length > 0 ? (
        <>
          <h1>Your recordings</h1>
          <div className="recordings-list">
            {recordings.map((record) => (
              <div className="record" key={record.key}>
                <div className="record-inner">
                  <audio controls src={record.audio} />
                  <div className="delete-button-container">
                      <button
                          className="delete-button"
                          title="Delete this audio"
                          onClick={() => deleteAudio(record.key)}
                      >
                          <FaTrashAlt />
                      </button>
                  </div>
                  <div className="submit-button-container">
                      <Button
                          className="submit-button"
                          variant="contained"
                          onClick={() => handleTranscription(record.audio, record.key)} 
                      >
                          Transcribe
                      </Button>
                  </div>
                </div>
                {transcriptionStatus[record.key] === 'transcribing' && (
                  <p>
                    Transcribing
                    <span className="dot dot1"> .</span>
                    <span className="dot dot2">.</span>
                    <span className="dot dot3">.</span>
                  </p>
                )}

                {transcriptionStatus[record.key] === 'completed' && <p>Transcript: {transcriptions[record.key]}</p>}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="no-records">
          <span>You don't have records</span>
        </div>
      )}
    </div>
  );
}
