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
import { alpha, useTheme } from "@mui/material/styles";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { useSpliceQueue } from "@/hooks/useSpliceQueue";
import AuthRequiredDialog from "@/components/Elements/AuthRequiredDialog";

export default function MainSection() {
  const theme = useTheme();
  const waveColor = theme.palette.border.main;
  const progressColor = theme.palette.primary.main;
  const regionSelectionColor = alpha(theme.palette.primary.main, 0.25);
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const regionsDragCleanupRef = useRef<(() => void) | null>(null);
  
  const [playing, setPlaying] = useState(false);
  const [labelValue, setLabelValue] = useState("");
  const [cutMode, setCutMode] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [endTime, setEndTime] = useState<number | null>(null);
  const { clip, isLoading, statusMessage, error, fetchNextClip, submitClip, deleteClip } = useSpliceQueue("label");
  const hasClip = Boolean(clip);
  const { data: session } = useSession();
  const router = useRouter();
  const DEFAULT_AUTH_MESSAGE = "Please register or log in to keep track of your contributions. You can also continue anonymously if you prefer.";
  const [openAuthDialog, setOpenAuthDialog] = useState(false);
  const [authDialogMessage, setAuthDialogMessage] = useState(DEFAULT_AUTH_MESSAGE);
  const accessToken = (session as { accessToken?: string } | null)?.accessToken;

  const showAuthDialog = (message?: string) => {
    setAuthDialogMessage(message ?? DEFAULT_AUTH_MESSAGE);
    setOpenAuthDialog(true);
  };

  const closeAuthDialog = () => {
    setAuthDialogMessage(DEFAULT_AUTH_MESSAGE);
    setOpenAuthDialog(false);
  };

  // Initialize WaveSurfer when container is ready
  useEffect(() => {
    if (!containerRef.current || wavesurferRef.current) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor,
      progressColor,
      barGap: 3,
      barWidth: 2,
      barHeight: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 60,
      hideScrollbar: true,
      // responsive: true, // Removed in v7, it's responsive by default
    });

    // Initialize Regions plugin
    const wsRegions = ws.registerPlugin(RegionsPlugin.create());
    regionsRef.current = wsRegions;

    // Region events
    wsRegions.on('region-created', (region) => {
      // Ensure only one region exists
      wsRegions.getRegions().forEach((r) => {
        if (r.id !== region.id) {
          r.remove();
        }
      });
      setStartTime(region.start);
      setEndTime(region.end);
    });

    wsRegions.on('region-updated', (region) => {
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
  }, [progressColor, waveColor]);

  // Handle Cut Mode Toggle
  useEffect(() => {
    if (!regionsRef.current) return;
    
    if (cutMode) {
      regionsDragCleanupRef.current = regionsRef.current.enableDragSelection({
        color: regionSelectionColor,
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
  }, [cutMode, regionSelectionColor]);

  // Load audio when clip changes
  useEffect(() => {
    if (!wavesurferRef.current) {
      return;
    }

    if (clip?.audioUrl) {
      wavesurferRef.current.load(clip.audioUrl).catch((err) => {
        if (err.name === 'AbortError') {
          console.log('WaveSurfer load aborted');
        } else {
          console.error('WaveSurfer load error', err);
        }
      });
      regionsRef.current?.clearRegions();
    } else if (typeof wavesurferRef.current.empty === "function") {
      wavesurferRef.current.empty();
    }

    setStartTime(null);
    setEndTime(null);
  }, [clip?.audioUrl, clip?.id]);

  useEffect(() => {
    fetchNextClip();
  }, [fetchNextClip]);

  useEffect(() => {
    setLabelValue("");
  }, [clip?.id]);

  const deleteAudio = async () => {
    if (!deleteClip || !clip) {
      return;
    }
    try {
      wavesurferRef.current?.stop();
      setLabelValue("");
      setCutMode(false);
      await deleteClip();
    } catch (error) {
      console.error("Failed to delete audio", error);
    }
  };

  const handleSubmit = async () => {
    if (!accessToken) {
      showAuthDialog();
      return;
    }
    await submitData(true);
  };

  const handleSkip = async () => {
    closeAuthDialog();
    await submitData(false);
  };

  const submitData = async (isAuthenticated: boolean) => {
    if (!clip) return;
    try {
      let start: number | undefined;
      let end: number | undefined;

      const shouldSendTrim =
        cutMode &&
        startTime !== null &&
        endTime !== null &&
        startTime !== endTime;

      if (shouldSendTrim) {
        const trimStart = Math.min(startTime as number, endTime as number);
        const trimEnd = Math.max(startTime as number, endTime as number);
        start = Number(trimStart.toFixed(3));
        end = Number(trimEnd.toFixed(3));
      }

      await submitClip({
        label: labelValue,
        start,
        end,
        isAuthenticated,
        accessToken,
      });

      wavesurferRef.current?.stop();
      setLabelValue("");
      setCutMode(false);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401 && isAuthenticated) {
        showAuthDialog("Your session expired. Please sign in again to continue labeling.");
      } else {
        console.error("Failed to perform PUT request:", error);
      }
    }
  };

  const handlePlayPause = () => {
    if (!clip) {
      return;
    }
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
          <SectionHeading>AUDIO LABELING</SectionHeading>
        </CardHeader>
        <CardBody>
          <WaveformContainer>
            <div ref={containerRef} style={{ width: "100%" }} />
            {!clip && (statusMessage || error) && (
              <EmptyState>{statusMessage ?? error}</EmptyState>
            )}
          </WaveformContainer>
          
          <InputSection>
            <LabelRow>
              <InputLabel style={{ marginBottom: 0 }}>Transcript</InputLabel>
              <FormControlLabel
                control={
                  <StyledSwitch
                    checked={cutMode}
                    onChange={(e) => setCutMode(e.target.checked)}
                    name="cutMode"
                    disabled={!hasClip}
                  />
                }
                label={<CutAudioLabel>Cut Audio</CutAudioLabel>}
                disabled={!hasClip}
              />
            </LabelRow>
            <StyledTextField
              id="transcript-input"
              variant="outlined"
              placeholder="Enter the content of the audio"
              value={labelValue}
              onChange={(event) => setLabelValue(event.target.value)}
              fullWidth
              disabled={!hasClip}
              InputProps={{
                style: { backgroundColor: 'var(--accent)', borderRadius: '8px' }
              }}
            />
          </InputSection>

          <ControlsRow>
            <CircleButton onClick={handlePlayPause} disabled={!hasClip}>
              {playing ? <PauseIcon style={{ color: 'var(--foreground)' }} /> : <PlayArrowIcon style={{ color: 'var(--foreground)' }} />}
            </CircleButton>
            
            <SubmitButton
              variant="contained"
              onClick={handleSubmit}
              disabled={!hasClip}
            >
              Submit
            </SubmitButton>

            <CircleButton onClick={deleteAudio} disabled={!hasClip}>
              <DeleteIcon style={{ color: 'var(--foreground)' }} />
            </CircleButton>
          </ControlsRow>
        </CardBody>
      </CardContainer>
      <AuthRequiredDialog
        open={openAuthDialog}
        onClose={closeAuthDialog}
        onSkip={handleSkip}
        onAuthenticate={() => router.push("/login")}
        message={authDialogMessage}
      />
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
  position: relative;
  min-height: 120px;
`;

const EmptyState = styled.div`
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--foreground);
  text-align: center;
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
