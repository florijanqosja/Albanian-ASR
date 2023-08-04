import { FaTrashAlt, FaExclamationCircle } from "react-icons/fa";
import useRecordingsList from "../../hooks/use-recordings-list";
import "./styles.css";
import Button from "@material-ui/core/Button";

export default function RecordingsList({ audio }) {
  const { recordings, deleteAudio } = useRecordingsList(audio);

  // Function to handle the submission
  const handleSubmit = () => {
    console.log("PUT request successful");
  };

  return (
    <div className="recordings-container">
      {recordings.length > 0 ? (
        <>
          <h1>Your recordings</h1>
          <div className="recordings-list">
            {recordings.map((record) => (
              <div className="record" key={record.key}>
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
                    onClick={handleSubmit}
                  >
                    Transcribe
                  </Button>
                </div>
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
