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
      <Title>Record your voice</Title>
      <RecorderContainer>
        <RecorderControls recorderState={recorderState} handlers={handlers} />
        <RecordingsList audio={audio} />
      </RecorderContainer>
      <SubmitButton
          variant="contained"
          color="primary"
          onClick={handleSubmit}
        >
          Submit
        </SubmitButton>
    </VoiceRecorder>
  );
};


const VoiceRecorder = styled.div`
  min-height: 100vh;
  display: grid;
  place-content: center;
`;

const Title = styled.div`
  margin-bottom: 2rem;
  font-size: 3rem;
  text-align: center;
`;

const RecorderContainer = styled.div`
  min-width: 300px;
  width: 30vw;
  height: 40vh;
  border-radius: 1rem;
  background: linear-gradient(to right, #301616, #9e3936);
  color: #fff;
`;

const SubmitButton = styled(Button)`
  && {
    background-color: #b33e3a;
    color: #fff;
    &:hover {
      background-color: #401a1a;
    }
  }
`;
