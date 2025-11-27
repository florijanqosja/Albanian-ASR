"use client";
import React, { useState, useEffect, useRef } from "react";
import styled, { keyframes } from "styled-components";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import DeleteIcon from "@mui/icons-material/Delete";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import { useTheme } from "@mui/material/styles";
import { useSession } from "next-auth/react";
import { Dialog, DialogTitle, DialogContent, DialogActions, Typography } from "@mui/material";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function AudioValidate() {
  const theme = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const regionsDragCleanupRef = useRef<(() => void) | null>(null);
  
  const [playing, setPlaying] = useState(false);
  const [labelValue, setLabelValue] = useState("");
  const [audioID, setAudioID] = useState<string | null>(null);
  const [audioPath, setAudioPath] = useState("");
  
  // Cut functionality state
  const [cutMode, setCutMode] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [endTime, setEndTime] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { data: session } = useSession();
  const router = useRouter();
  const [openAuthDialog, setOpenAuthDialog] = useState(false);

  // Initialize WaveSurfer when container is ready
  useEffect(() => {
    if (!containerRef.current || wavesurferRef.current) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: theme.palette.border.main,
      progressColor: theme.palette.primary.main,
      barGap: 3,
      barWidth: 2,
      barHeight: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 60,
      hideScrollbar: true,
    });

    // Initialize Regions plugin
    const wsRegions = ws.registerPlugin(RegionsPlugin.create());
    regionsRef.current = wsRegions;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    wsRegions.on('region-created', (region: any) => {
      // Ensure only one region exists
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      wsRegions.getRegions().forEach((r: any) => {
        if (r.id !== region.id) {
          r.remove();
        }
      });
      setStartTime(region.start);
      setEndTime(region.end);
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    wsRegions.on('region-updated', (region: any) => {
      setStartTime(region.start);
      setEndTime(region.end);
    });

    ws.on('play', () => setPlaying(true));
    ws.on('pause', () => setPlaying(false));
    ws.on('finish', () => setPlaying(false));

    wavesurferRef.current = ws;

    // Cleanup on unmount
    return () => {
      ws.destroy();
      wavesurferRef.current = null;
    };
  }, []);

  // Handle Cut Mode Toggle
  useEffect(() => {
    if (!regionsRef.current) return;
    
    if (cutMode) {
      regionsDragCleanupRef.current = regionsRef.current.enableDragSelection({
        color: 'rgba(189, 62, 58, 0.3)',
      });
    } else {
      if (regionsDragCleanupRef.current) {
        regionsDragCleanupRef.current();
        regionsDragCleanupRef.current = null;
      }
      regionsRef.current.clearRegions();
      setStartTime(null);
      setEndTime(null);
    }
  }, [cutMode]);

    // Load audio when path changes
  useEffect(() => {
    if (wavesurferRef.current && audioPath) {
      wavesurferRef.current.load(audioPath).catch((err) => {
        if (err.name === 'AbortError') {
          console.log('WaveSurfer load aborted');
        } else {
          console.error('WaveSurfer load error', err);
        }
      });
      // Reset regions when new audio loads
      if (regionsRef.current) {
        regionsRef.current.clearRegions();
      }
      setStartTime(null);
      setEndTime(null);
    }
  }, [audioPath]);

  useEffect(() => {
    fetchAudioData();
  }, []);

  const fetchAudioData = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL}audio/to_validate`);
      if (response.data && response.data.data) {
        const { path, id, label } = response.data.data;
        const audioURL = `${process.env.NEXT_PUBLIC_FILE_ACCESS_DOMAIN_LOCAL}${path}`;
        setAudioPath(audioURL);
        setAudioID(id);
        setLabelValue(label || "");
        console.log("set the audioID to ", id);
      } else {
        console.log("No audio data available to validate.");
      }
    } catch (error) {
      console.error("Failed to fetch audio data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAudio = async () => {
    setIsLoading(true);
    try {
      await axios.delete(`${process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL}audio`, {
        data: {
          id: audioID,
        },
      });
      console.log("Delete request successful");
      if (wavesurferRef.current) {
          wavesurferRef.current.stop();
      }
      setLabelValue(""); 
      await fetchAudioData();
    } catch (error) {
      console.error("Failed to perform DELETE request:", error);
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!session) {
        setOpenAuthDialog(true);
        return;
    }
    await submitData(true);
  };

  const handleSkip = async () => {
    setOpenAuthDialog(false);
    await submitData(false);
  };

  const submitData = async (isAuthenticated: boolean) => {
    setIsLoading(true);
    try {
      const payload: { id: string | null; label: string; start?: number; end?: number } = {
        id: audioID,
        label: labelValue,
      };

      if (cutMode && startTime !== null && endTime !== null) {
        payload.start = startTime;
        payload.end = endTime;
      }

      const endpoint = isAuthenticated ? "audio/validate" : "audio/validate/anonymous";
      const headers = isAuthenticated ? { Authorization: `Bearer ${(session as any).accessToken}` } : {};

      await axios.put(`${process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL}${endpoint}`, payload, { headers });
      console.log("PUT request successful");
      if (wavesurferRef.current) {
          wavesurferRef.current.stop();
      }
      setLabelValue(""); 
      setCutMode(false);
      setTimeout(() => {
        fetchAudioData(); 
      }, 500);
    } catch (error) {
      console.error("Failed to perform PUT request:", error);
      setIsLoading(false);
    }
  };

  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      if (cutMode && startTime !== null && endTime !== null && regionsRef.current) {
        const regions = regionsRef.current.getRegions();
        if (regions.length > 0) {
          // Play the region and stop at the end
          regions[0].play(true);
          return;
        }
      }
      wavesurferRef.current.playPause();
    }
  };

  return (
    <Wrapper id="main-section">
      <CardContainer>
        {isLoading && (
          <LoadingOverlay>
            <LoadingSpinner>
              <Bar style={{ animationDelay: '0s' }} />
              <Bar style={{ animationDelay: '0.1s' }} />
              <Bar style={{ animationDelay: '0.2s' }} />
              <Bar style={{ animationDelay: '0.3s' }} />
              <Bar style={{ animationDelay: '0.4s' }} />
            </LoadingSpinner>
          </LoadingOverlay>
        )}
        <CardHeader>
          <SectionHeading>LABELED AUDIO VALIDATING</SectionHeading>
        </CardHeader>
        <CardBody>
          <WaveformContainer>
            <div ref={containerRef} style={{ width: "100%" }} />
          </WaveformContainer>
          
          <InputSection>
            <LabelRow>
              <InputLabel style={{ marginBottom: 0 }}>Transcript</InputLabel>
              <FormControlLabel
                control={
                  <StyledSwitch
                    checked={cutMode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCutMode(e.target.checked)}
                    name="cutMode"
                  />
                }
                label={<CutAudioLabel>Cut Audio</CutAudioLabel>}
              />
            </LabelRow>
            <StyledTextField
              id="transcript-input"
              variant="outlined"
              placeholder="Enter the content of the audio"
              value={labelValue}
              onChange={(event) => setLabelValue(event.target.value)}
              fullWidth
              InputProps={{
                style: { backgroundColor: 'var(--accent)', borderRadius: '8px' }
              }}
            />
          </InputSection>

          <ControlsRow>
            <CircleButton onClick={handlePlayPause}>
              {playing ? <PauseIcon style={{ color: 'var(--foreground)' }} /> : <PlayArrowIcon style={{ color: 'var(--foreground)' }} />}
            </CircleButton>
            
            <SubmitButton
              variant="contained"
              onClick={handleSubmit}
            >
              Submit
            </SubmitButton>

            <CircleButton onClick={deleteAudio}>
              <DeleteIcon style={{ color: 'var(--foreground)' }} />
            </CircleButton>
          </ControlsRow>
        </CardBody>
      </CardContainer>
      <Dialog open={openAuthDialog} onClose={() => setOpenAuthDialog(false)}>
        <DialogTitle>Authentication Required</DialogTitle>
        <DialogContent>
            <Typography>Please register or log in to track your contributions. You can also continue anonymously.</Typography>
        </DialogContent>
        <DialogActions>
            <Button onClick={handleSkip}>Skip (Anonymous)</Button>
            <Button onClick={() => router.push("/login")} variant="contained">Register / Log In</Button>
        </DialogActions>
      </Dialog>
    </Wrapper>
  );
}

const Wrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
  background-color: var(--background);
`;

const CardContainer = styled.div`
  width: 800px;
  background-color: var(--card);
  border-radius: 20px;
  box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  border: 1px solid var(--border);
  position: relative;
`;

const CardHeader = styled.div`
  background-color: var(--accent); /* Light pink/salmon */
  padding: 20px;
  text-align: center;
`;

const CardBody = styled.div`
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const SectionHeading = styled.h2`
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
  color: var(--foreground);
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const WaveformContainer = styled.div`
  width: 100%;
  background-color: var(--accent);
  border-radius: 50px;
  padding: 20px 40px;
  margin-bottom: 30px;
`;

const InputSection = styled.div`
  width: 100%;
  margin-bottom: 30px;
`;

const InputLabel = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--foreground);
  margin-bottom: 10px;
`;

const StyledTextField = styled(TextField)`
  & .MuiOutlinedInput-root {
    & fieldset {
      border-color: var(--border);
    }
    &:hover fieldset {
      border-color: var(--primary);
    }
    &.Mui-focused fieldset {
      border-color: var(--accent);
    }
  }
`;

const ControlsRow = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  width: 100%;
`;

const CircleButton = styled(IconButton)`
  && {
    background-color: var(--accent);
    width: 50px;
    height: 50px;
    &:hover {
      background-color: var(--accent);
      opacity: 0.9;
    }
  }
`;

const SubmitButton = styled(Button)`
  && {
    background-color: var(--primary);
    color: var(--primary-foreground);
    padding: 10px 40px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    text-transform: none;
    height: 50px;
    &:hover {
      background-color: var(--primary);
      opacity: 0.9;
    }
  }
`;

const LabelRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
`;

const CutAudioLabel = styled.span`
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--foreground);
  font-family: inherit;
`;

const StyledSwitch = styled(Switch)`
  & .MuiSwitch-switchBase.Mui-checked {
    color: var(--primary);
    &:hover {
      background-color: var(--primary);
      opacity: 0.04;
    }
  }
  & .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track {
    background-color: var(--primary);
  }
`;

const wave = keyframes`
  0%, 100% { height: 10px; transform: scaleY(1); }
  50% { height: 30px; transform: scaleY(1.5); }
`;

const LoadingOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
  backdrop-filter: blur(2px);
`;

const LoadingSpinner = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 40px;
`;

const Bar = styled.div`
  width: 6px;
  height: 20px;
  background-color: var(--primary);
  border-radius: 4px;
  animation: ${wave} 1s ease-in-out infinite;
`;
