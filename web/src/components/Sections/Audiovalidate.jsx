import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import ReactWaves, { Regions } from "@dschoon/react-waves";
import PlayArrowIcon from "@material-ui/icons/PlayArrow";
import PauseIcon from "@material-ui/icons/Pause";
import DeleteIcon from "@material-ui/icons/Delete";
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import IconButton from "@material-ui/core/IconButton";
import VisibilityIcon from "@material-ui/icons/Visibility";
import VisibilityOffIcon from "@material-ui/icons/VisibilityOff";
import axios from "axios";

export default function AudioValidater() {
  const [wavesurfer, setWavesurfer] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [pos, setPos] = useState(0);
  const [showRegion, setShowRegion] = useState(false);
  const [labelValue, setLabelValue] = useState("");
  const [audioID, setAudioID] = useState(null);
  const [audioPath, setAudioPath] = useState("");
  const wavesurferRef = useRef(null);

  const region = {
    id: "One",
    start: 40,
    end: 60,
    color: "rgba(179, 62, 58, 0.3)",
  };

  useEffect(() => {
    fetchAudioData();
  }, []);

  const fetchAudioData = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_DOMAIN_PROD}audio/to_validate`);
      const { Sp_PATH, Sp_ID, Sp_LABEL } = response.data;
      const audioURL = `${process.env.REACT_APP_FILE_ACCESS_DOMAIN_PROD}${Sp_PATH}`;
      setAudioPath(audioURL);
      setAudioID(Sp_ID);
      setLabelValue(Sp_LABEL);
      console.log("set the audioID to ", Sp_ID);

      if (wavesurfer) {
        wavesurfer.load(audioURL);
      }
    } catch (error) {
      console.error("Failed to fetch audio data:", error);
    }
  };

  const deleteAudio = async () => {
    try {
      await axios.delete(`${process.env.REACT_APP_API_DOMAIN_PROD}audio`, {
        data: {
          Sp_ID: audioID,
        },
      });
      console.log("Delete request successful");
      setPlaying(false); // Stop the audio playback
      setLabelValue(""); // Reset the label value
      fetchAudioData();
      setPos(0);
    } catch (error) {
      console.error("Failed to perform DELETE request:", error);
    }
  };

  const handleSubmit = async () => {
    try {
      await axios.put(`${process.env.REACT_APP_API_DOMAIN_PROD}audio/validate`, {
        Sp_ID: audioID,
        Sp_LABEL: labelValue,
      });
      console.log("PUT request successful");
      setPlaying(false); // Stop the audio playback
      setLabelValue(""); // Reset the label value
      setTimeout(() => {
        fetchAudioData(); // Fetch new audio data
        setPos(0); // Reset the position to 0
        setPlaying(true); // Set the play button to the play state
      }, 500);
    } catch (error) {
      console.error("Failed to perform PUT request:", error);
    }
  };

  const onLoading = ({ wavesurfer, originalArgs = [] }) => {
    wavesurferRef.current = wavesurfer;
    setWavesurfer(wavesurferRef.current); // New line
  };

  const onPosChange = (newPos) => {
    if (wavesurfer) {
      const duration = wavesurfer.getDuration();
      const positionInSeconds = newPos * duration;
      setPos(positionInSeconds);
    }
  };

  const handleRegionClick = () => {
    if (wavesurfer && wavesurfer.isPlaying()) {
      wavesurfer.stop();
    }
    setPlaying(false);
  };

  const removeRegion = (name) => {
    if (
      wavesurfer &&
      wavesurfer.regions &&
      wavesurfer.regions.list[name]
    ) {
      wavesurfer.regions.list[name].remove();
    }
  };

  const toggleRegion = () => {
    setShowRegion(!showRegion);
    removeRegion("One");
  };

  return (
    <Wrapper id="main-section">
        
      <PlayerWrapper>
      <SectionHeading>LABELED AUDIO VALIDATING</SectionHeading>
        <div className="container example">
          <CenteredReactWavesWrapper>
            <ReactWaves
              audioFile={audioPath}
              className="react-waves"
              options={{
                barGap: 3,
                barWidth: 2,
                barHeight: 2,
                barRadius: 3,
                cursorWidth: 1,
                height: 60,
                hideScrollbar: true,
                progressColor: "#b33e3a",
                responsive: true,
                waveColor: "#281413",
              }}
              volume={1}
              pos={pos}
              playing={playing}
              onPosChange={onPosChange}
              onLoading={onLoading}
              onFinish={() => setPlaying(false)}
            >
              {showRegion && wavesurfer && (
                <Regions
                  regions={[region]}
                  onRegionClick={handleRegionClick}
                />
              )}
            </ReactWaves>
          </CenteredReactWavesWrapper>
        </div>
        <ButtonWrapper>
          <IconButton>
            <DeleteIcon onClick={deleteAudio} />
          </IconButton>
          <IconButton onClick={() => setPlaying(!playing)}>
            {playing ? <PauseIcon /> : <PlayArrowIcon />}
          </IconButton>
          <IconButton onClick={toggleRegion}>
            {showRegion ? <VisibilityOffIcon /> : <VisibilityIcon />}
          </IconButton>
        </ButtonWrapper>
        <TextField
          label="Enter the content of the audio"
          variant="outlined"
          style={{
            width: "70%",
            marginTop: "30px",
            marginBottom: "30px",
            textAlign: "center",
          }}
          value={labelValue}
          onChange={(event) => setLabelValue(event.target.value)}
        />
        <SubmitButton
          variant="contained"
          color="primary"
          onClick={handleSubmit}
        >
          Submit
        </SubmitButton>
      </PlayerWrapper>
    </Wrapper>
  );
}

const Wrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 500px;
  margin-top: 80px;
`;

const PlayerWrapper = styled.div`
  width: 800px;
  background-color: #cda5a3;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const CenteredReactWavesWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
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

const ButtonWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  width: 160px;
  margin-top: 10px;
`;

const SectionHeading = styled.h2`
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 0px;
  color: #301616;
`;