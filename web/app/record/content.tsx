"use client";

import { useSession } from "next-auth/react";
import { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";
import { useTranslations } from "next-intl";
import {
  Container,
  Typography,
  Button,
  Box,
  Stack,
  Alert,
  IconButton,
  Chip,
  TextField,
  LinearProgress,
  Switch,
  FormControlLabel,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import styled, { keyframes } from "styled-components";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";
import DeleteIcon from "@mui/icons-material/Delete";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import StopIcon from "@mui/icons-material/Stop";
import { RefreshCw, CheckCircle2 } from "lucide-react";
import Statistics from "@/components/Sections/Statistics";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"
).replace(/\/*$/, "/");

type RecordPrompt = {
  id: number;
  prompt_text: string;
  status: string;
};

export default function RecordPage() {
  const t = useTranslations();
  const { data: session, status } = useSession();
  const theme = useTheme();
  const accessToken = (session as { accessToken?: string } | null)?.accessToken;
  const isAuthenticated = status === "authenticated" && Boolean(accessToken);

  const waveColor = theme.palette.divider;
  const progressColor = theme.palette.primary.main;
  const regionSelectionColor = alpha(theme.palette.primary.main, 0.25);

  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const regionsDragCleanupRef = useRef<(() => void) | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingStartRef = useRef<number | null>(null);

  const [prompt, setPrompt] = useState<RecordPrompt | null>(null);
  const [transcriptValue, setTranscriptValue] = useState("");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedDuration, setRecordedDuration] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isPromptLoading, setIsPromptLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cutMode, setCutMode] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [endTime, setEndTime] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);

  const hasRecording = Boolean(audioBlob);

  const fetchPrompt = useCallback(async () => {
    if (!accessToken) {
      setPrompt(null);
      setStatusMessage(t("record.statusSignedOut"));
      return;
    }
    setIsPromptLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      const { data } = await axios.get(`${API_BASE}record/text`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const promptPayload = data?.data as RecordPrompt | null;
      if (promptPayload) {
        setPrompt(promptPayload);
        setTranscriptValue(promptPayload.prompt_text ?? "");
        setStatusMessage(t("record.statusPromptReady"));
      } else {
        setPrompt(null);
        setTranscriptValue("");
        setStatusMessage(data?.message ?? t("record.statusNoPrompts"));
      }
    } catch (err) {
      console.error("Failed to fetch prompt", err);
      setErrorMessage(t("record.statusFetchError"));
    } finally {
      setIsPromptLoading(false);
    }
  }, [accessToken, t]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchPrompt();
    } else {
      setPrompt(null);
      setTranscriptValue("");
    }
  }, [isAuthenticated, fetchPrompt]);

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
    });

    const wsRegions = ws.registerPlugin(RegionsPlugin.create());
    regionsRef.current = wsRegions;

    wsRegions.on("region-created", (region) => {
      wsRegions.getRegions().forEach((existing) => {
        if (existing.id !== region.id) {
          existing.remove();
        }
      });
      setStartTime(region.start);
      setEndTime(region.end);
    });

    wsRegions.on("region-updated", (region) => {
      setStartTime(region.start);
      setEndTime(region.end);
    });

    ws.on("play", () => setPlaying(true));
    ws.on("pause", () => setPlaying(false));
    ws.on("finish", () => setPlaying(false));

    wavesurferRef.current = ws;

    return () => {
      ws.destroy();
      wavesurferRef.current = null;
    };
  }, [progressColor, waveColor]);

  useEffect(() => {
    if (!regionsRef.current) return;

    if (cutMode) {
      regionsDragCleanupRef.current = regionsRef.current.enableDragSelection({
        color: regionSelectionColor,
      });
    } else {
      regionsDragCleanupRef.current?.();
      regionsDragCleanupRef.current = null;
      regionsRef.current.clearRegions();
      setStartTime(null);
      setEndTime(null);
    }
  }, [cutMode, regionSelectionColor]);

  useEffect(() => {
    const loadAudio = async () => {
      if (!wavesurferRef.current) {
        return;
      }
      if (audioBlob) {
        try {
          await wavesurferRef.current.loadBlob(audioBlob);
        } catch (error) {
          console.error("Failed to load recorded audio", error);
        }
      } else if (typeof wavesurferRef.current.empty === "function") {
        wavesurferRef.current.empty();
      }
      regionsRef.current?.clearRegions();
      setStartTime(null);
      setEndTime(null);
    };

    loadAudio();
  }, [audioBlob]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    if (!isAuthenticated) {
      setErrorMessage(t("record.errorLoginRecord"));
      return;
    }
    if (!prompt) {
      setErrorMessage(t("record.errorNeedPrompt"));
      return;
    }
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setErrorMessage(t("record.errorNoSupport"));
      return;
    }
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(blob);
        if (recordingStartRef.current) {
          const elapsed = (Date.now() - recordingStartRef.current) / 1000;
          setRecordedDuration(Number(elapsed.toFixed(2)));
        }
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);
        setStatusMessage(t("record.statusCaptured"));
      };
      recorder.start();
      recordingStartRef.current = Date.now();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setAudioBlob(null);
      setRecordedDuration(null);
      setStatusMessage(t("record.statusInProgress"));
    } catch (err) {
      console.error("Microphone access denied", err);
      setErrorMessage(t("record.errorMic"));
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (!isRecording || !mediaRecorderRef.current) {
      return;
    }
    if (mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setStatusMessage(t("record.statusProcessing"));
    }
  };

  const clearRecording = (silent = false) => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (typeof wavesurferRef.current?.empty === "function") {
      wavesurferRef.current.empty();
    }
    regionsRef.current?.clearRegions();
    setAudioBlob(null);
    setRecordedDuration(null);
    setCutMode(false);
    setStartTime(null);
    setEndTime(null);
    setPlaying(false);
    if (!silent) {
      setStatusMessage(t("record.statusCleared"));
    }
  };

  const handlePlayPause = () => {
    if (!hasRecording || !wavesurferRef.current) {
      return;
    }
    if (cutMode && startTime !== null && endTime !== null && startTime !== endTime && regionsRef.current) {
      const regions = regionsRef.current.getRegions();
      if (regions.length > 0) {
        regions[0].play(true);
        return;
      }
    }
    wavesurferRef.current.playPause();
  };

  const prepareUploadBlob = async (): Promise<Blob> => {
    if (!audioBlob) {
      throw new Error("No recording available");
    }
    const shouldTrim =
      cutMode &&
      startTime !== null &&
      endTime !== null &&
      startTime !== endTime &&
      typeof window !== "undefined";

    if (!shouldTrim) {
      return audioBlob;
    }

    try {
      return await trimAudioBlob(audioBlob, Math.min(startTime!, endTime!), Math.max(startTime!, endTime!));
    } catch (error) {
      console.error("Failed to trim audio", error);
      setErrorMessage("Unable to trim audio. Submitting original clip instead.");
      return audioBlob;
    }
  };

  const submitRecording = async () => {
    if (!isAuthenticated || !accessToken) {
      setErrorMessage(t("record.errorLoginSubmit"));
      return;
    }
    if (!prompt) {
      setErrorMessage(t("record.errorReserve"));
      return;
    }
    if (!audioBlob) {
      setErrorMessage(t("record.errorNoRecording"));
      return;
    }
    const transcript = transcriptValue.trim();
    if (!transcript) {
      setErrorMessage(t("record.errorEmptyTranscript"));
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const preparedBlob = await prepareUploadBlob();
      const mimeType = preparedBlob.type || audioBlob.type || "audio/webm";
      const ext = mimeType.includes("wav") ? "wav" : "webm";

      const formData = new FormData();
      formData.append("text_splice_id", String(prompt.id));
      formData.append("spoken_text", transcript);
      const audioFile = new File([preparedBlob], `recording-${Date.now()}.${ext}`, { type: mimeType });
      formData.append("audio_file", audioFile);

      const { data } = await axios.post(`${API_BASE}record/upload`, formData, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "multipart/form-data",
        },
      });
      setSuccessMessage(data?.message ?? t("record.successSubmit"));
      setStatusMessage(null);
      clearRecording(true);
      await fetchPrompt();
    } catch (err) {
      console.error("Failed to submit recording", err);
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.response?.data?.message || t("record.errorSubmit")
        : t("record.errorSubmit");
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const recordingDisabled = !isAuthenticated || !prompt;

  return (
    <>
      <Box sx={{ bgcolor: "background.paper" }}>
        <Container maxWidth="md" sx={{ py: { xs: 6, md: 10 } }}>
          <Stack spacing={4}>
        <Box textAlign="center">
          <Typography variant="h3" fontWeight={800} sx={{ color: "text.primary" }}>
            {t("record.title")}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 1 }}>
            {t("record.subtitle")}
          </Typography>
        </Box>

        {status !== "authenticated" && (
          <Alert severity="info">
            {t("record.authInfo")}
          </Alert>
        )}
        {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
        {successMessage && (
          <Alert icon={<CheckCircle2 size={18} />} severity="success">
            {successMessage}
          </Alert>
        )}

            <RecordWrapper>
              <RecordCard>
            {isSubmitting && (
              <LoadingOverlay>
                <LoadingSpinner>
                  <Bar style={{ animationDelay: "0s" }} />
                  <Bar style={{ animationDelay: "0.1s" }} />
                  <Bar style={{ animationDelay: "0.2s" }} />
                  <Bar style={{ animationDelay: "0.3s" }} />
                  <Bar style={{ animationDelay: "0.4s" }} />
                </LoadingSpinner>
              </LoadingOverlay>
            )}
            <RecordHeader>
              <SectionHeading>{t("record.recordSection")}</SectionHeading>
            </RecordHeader>
            <RecordBody>
              <PromptPanel>
                <PromptHeader>
                  <div>
                    <PromptLabelText>{t("record.promptLabel")}</PromptLabelText>
                    <PromptStatus>{prompt ? t("record.promptActive") : t("record.promptAwaiting")}</PromptStatus>
                  </div>
                  <PromptActions>
                    <Chip
                      label={prompt ? t("record.promptChipActive") : t("record.promptChipAwaiting")}
                      color={prompt ? "primary" : "default"}
                      variant="outlined"
                      size="small"
                    />
                    <IconButton
                      aria-label={t("record.refresh")}
                      onClick={fetchPrompt}
                      disabled={!isAuthenticated || isPromptLoading}
                      sx={{ border: "1px solid", borderColor: "divider" }}
                    >
                      <RefreshCw size={18} />
                    </IconButton>
                  </PromptActions>
                </PromptHeader>
                <PromptText>
                  {prompt?.prompt_text ?? t("record.noPrompt")}
                </PromptText>
                {isPromptLoading && <LinearProgress color="primary" />}
              </PromptPanel>

              <RecordToolbar>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<FiberManualRecordIcon />}
                  onClick={startRecording}
                  disabled={isRecording || recordingDisabled}
                  sx={{
                    borderRadius: "999px",
                    textTransform: "none",
                    fontWeight: 600,
                    px: 3,
                    minWidth: 180,
                  }}
                >
                  {isRecording ? t("record.recording") : t("record.startRecording")}
                </Button>
                <Button
                  variant="outlined"
                  color="inherit"
                  startIcon={<StopIcon />}
                  onClick={stopRecording}
                  disabled={!isRecording}
                  sx={{
                    borderRadius: "999px",
                    textTransform: "none",
                    fontWeight: 600,
                    px: 3,
                    minWidth: 140,
                  }}
                >
                  {t("record.stop")}
                </Button>
                <DurationBadge>
                  {recordedDuration !== null
                    ? `${t("record.duration")}: ${recordedDuration}s`
                    : isRecording
                      ? t("record.recording")
                      : t("record.noClip")}
                </DurationBadge>
              </RecordToolbar>
              {statusMessage && <StatusHelper>{statusMessage}</StatusHelper>}

              <WaveformContainer>
                <div ref={containerRef} style={{ width: "100%" }} />
                {!hasRecording && (
                  <EmptyState>
                    {statusMessage ?? t("record.waveEmpty")}
                  </EmptyState>
                )}
              </WaveformContainer>

              <InputSection>
                <LabelRow>
                  <InputLabel style={{ marginBottom: 0 }}>{t("record.transcript")}</InputLabel>
                  <FormControlLabel
                    control={
                      <StyledSwitch
                        checked={cutMode}
                        onChange={(event) => setCutMode(event.target.checked)}
                        name="cutMode"
                        disabled={!hasRecording}
                      />
                    }
                    label={<CutAudioLabel>{t("record.cutAudio")}</CutAudioLabel>}
                    disabled={!hasRecording}
                  />
                </LabelRow>
                <StyledTextField
                  id="transcript-input"
                  variant="outlined"
                  placeholder={t("record.placeholder")}
                  value={transcriptValue}
                  onChange={(event) => setTranscriptValue(event.target.value)}
                  fullWidth
                  multiline
                  minRows={3}
                  maxRows={10}
                  disabled={!prompt}
                  InputProps={{
                    style: { backgroundColor: "var(--accent)", borderRadius: "8px" },
                  }}
                />
              </InputSection>

              <ControlsRow>
                <CircleButton onClick={handlePlayPause} disabled={!hasRecording}>
                  {playing ? (
                    <PauseIcon style={{ color: "var(--foreground)" }} />
                  ) : (
                    <PlayArrowIcon style={{ color: "var(--foreground)" }} />
                  )}
                </CircleButton>

                <SubmitButton
                  variant="contained"
                  onClick={submitRecording}
                  disabled={!hasRecording || isSubmitting || recordingDisabled}
                >
                  {isSubmitting ? t("record.submitting") : t("record.submitRecording")}
                </SubmitButton>

                <CircleButton onClick={() => clearRecording()} disabled={!hasRecording || isRecording}>
                  <DeleteIcon style={{ color: "var(--foreground)" }} />
                </CircleButton>
              </ControlsRow>
            </RecordBody>
              </RecordCard>
            </RecordWrapper>
          </Stack>
        </Container>
      </Box>
      <Statistics />
    </>
  );
}

async function trimAudioBlob(blob: Blob, start: number, end: number): Promise<Blob> {
  if (typeof window === "undefined" || start === end) {
    return blob;
  }
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new AudioContext();
  try {
    const decodedBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const clampedStart = Math.max(0, Math.min(start, decodedBuffer.duration));
    const clampedEnd = Math.max(clampedStart, Math.min(end, decodedBuffer.duration));
    if (clampedEnd - clampedStart <= 0.01) {
      return blob;
    }

    const sampleRate = decodedBuffer.sampleRate;
    const startSample = Math.floor(clampedStart * sampleRate);
    const endSample = Math.floor(clampedEnd * sampleRate);
    const frameCount = endSample - startSample;

    const trimmedBuffer = audioContext.createBuffer(
      decodedBuffer.numberOfChannels,
      frameCount,
      sampleRate,
    );

    for (let channel = 0; channel < decodedBuffer.numberOfChannels; channel += 1) {
      const channelData = decodedBuffer.getChannelData(channel).subarray(startSample, endSample);
      trimmedBuffer.getChannelData(channel).set(channelData);
    }

    const wavArrayBuffer = audioBufferToWav(trimmedBuffer);
    return new Blob([wavArrayBuffer], { type: "audio/wav" });
  } finally {
    audioContext.close().catch(() => undefined);
  }
}

function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const numChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const format = 1; // PCM
  const bitDepth = 16;
  const blockAlign = (numChannels * bitDepth) / 8;
  const byteRate = sampleRate * blockAlign;
  const dataLength = buffer.length * blockAlign;
  const bufferLength = 44 + dataLength;
  const arrayBuffer = new ArrayBuffer(bufferLength);
  const view = new DataView(arrayBuffer);

  let offset = 0;
  const writeString = (str: string) => {
    for (let i = 0; i < str.length; i += 1) {
      view.setUint8(offset, str.charCodeAt(i));
      offset += 1;
    }
  };

  writeString("RIFF");
  view.setUint32(offset, 36 + dataLength, true);
  offset += 4;
  writeString("WAVE");
  writeString("fmt ");
  view.setUint32(offset, 16, true);
  offset += 4;
  view.setUint16(offset, format, true);
  offset += 2;
  view.setUint16(offset, numChannels, true);
  offset += 2;
  view.setUint32(offset, sampleRate, true);
  offset += 4;
  view.setUint32(offset, byteRate, true);
  offset += 4;
  view.setUint16(offset, blockAlign, true);
  offset += 2;
  view.setUint16(offset, bitDepth, true);
  offset += 2;
  writeString("data");
  view.setUint32(offset, dataLength, true);
  offset += 4;

  const interleaved = new Float32Array(buffer.length * numChannels);
  let dest = 0;
  for (let i = 0; i < buffer.length; i += 1) {
    for (let channel = 0; channel < numChannels; channel += 1) {
      interleaved[dest] = buffer.getChannelData(channel)[i];
      dest += 1;
    }
  }

  interleaved.forEach((sample) => {
    const clampedSample = Math.max(-1, Math.min(1, sample));
    view.setInt16(
      offset,
      clampedSample < 0 ? clampedSample * 0x8000 : clampedSample * 0x7fff,
      true,
    );
    offset += 2;
  });

  return arrayBuffer;
}

const RecordWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px 0 30px;
  background-color: transparent;
  width: 100%;
`;

const RecordCard = styled.div`
  width: 100%;
  max-width: 900px;
  background-color: var(--card);
  border-radius: 20px;
  box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  border: 1px solid var(--border);
  position: relative;
`;

const RecordHeader = styled.div`
  background-color: var(--accent);
  padding: 20px;
  text-align: center;
`;

const RecordBody = styled.div`
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
`;

const PromptPanel = styled.div`
  width: 100%;
  border-radius: 24px;
  border: 1px solid var(--border);
  background: linear-gradient(145deg, var(--card), rgba(166, 77, 74, 0.08));
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const PromptHeader = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
`;

const PromptLabelText = styled.p`
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--foreground);
`;

const PromptStatus = styled.span`
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 6px;
`;

const PromptText = styled.p`
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--foreground);
  white-space: pre-wrap;
  word-break: break-word;
`;

const PromptActions = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
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
  margin-bottom: 10px;
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

const RecordToolbar = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  width: 100%;
  justify-content: center;
`;

const DurationBadge = styled.span`
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid var(--border);
  font-weight: 600;
  color: var(--foreground);
  background: rgba(255, 255, 255, 0.6);
`;

const StatusHelper = styled.p`
  margin: 0;
  font-size: 0.95rem;
  color: var(--foreground);
  text-align: center;
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