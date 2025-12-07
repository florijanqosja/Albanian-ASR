import { useState, useCallback } from "react";
import axios from "axios";
import { buildFileAccessUrl } from "@/lib/utils";

export type SpliceStage = "label" | "validate";

interface SpliceClip {
  id: number;
  name?: string | null;
  label?: string | null;
  duration?: string | null;
  audioUrl: string;
}

interface SubmitArgs {
  label: string;
  start?: number;
  end?: number;
  isAuthenticated: boolean;
  accessToken?: string;
  validatorId?: string;
}

interface QueueCopy {
  noAudio?: string;
  fetchError?: string;
  submitError?: string;
  deleteError?: string;
}

interface UseSpliceQueueResult {
  clip: SpliceClip | null;
  isLoading: boolean;
  statusMessage: string | null;
  error: string | null;
  fetchNextClip: (showLoader?: boolean) => Promise<SpliceClip | null>;
  submitClip: (args: SubmitArgs) => Promise<void>;
  deleteClip?: () => Promise<void>;
}

const API_BASE = (process.env.NEXT_PUBLIC_API_DOMAIN_LOCAL ?? "").replace(/\/*$/, "/");
const FILE_BASE = process.env.NEXT_PUBLIC_FILE_ACCESS_DOMAIN_LOCAL;

const STAGE_CONFIG: Record<SpliceStage, {
  fetchPath: string;
  submitPath: { authenticated: string; anonymous: string };
  allowDelete: boolean;
}> = {
  label: {
    fetchPath: "audio/to_label",
    submitPath: {
      authenticated: "audio/label",
      anonymous: "audio/label/anonymous",
    },
    allowDelete: true,
  },
  validate: {
    fetchPath: "audio/to_validate",
    submitPath: {
      authenticated: "audio/validate",
      anonymous: "audio/validate/anonymous",
    },
    allowDelete: false,
  },
};

export function useSpliceQueue(stage: SpliceStage, copy: QueueCopy = {}): UseSpliceQueueResult {
  const [clip, setClip] = useState<SpliceClip | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchNextClip = useCallback(async (showLoader = true) => {
    if (showLoader) {
      setIsLoading(true);
    }
    setError(null);

    try {
      const { data } = await axios.get(`${API_BASE}${STAGE_CONFIG[stage].fetchPath}`);
      const clipData = data?.data;
      if (clipData) {
        const audioUrl = buildFileAccessUrl(FILE_BASE, clipData.path);
        const normalizedClip: SpliceClip = {
          id: clipData.id,
          name: clipData.name,
          label: clipData.label,
          duration: clipData.duration,
          audioUrl,
        };
        setClip(normalizedClip);
        setStatusMessage(null);
        return normalizedClip;
      }
      setClip(null);
      setStatusMessage(data?.message ?? copy.noAudio ?? "No audio available.");
      return null;
    } catch (err) {
      console.error(`Failed to fetch ${stage} audio`, err);
      setClip(null);
      setError(copy.fetchError ?? "Unable to fetch audio. Please try again.");
      return null;
    } finally {
      if (showLoader) {
        setIsLoading(false);
      }
    }
  }, [copy.fetchError, copy.noAudio, stage]);

  const submitClip = useCallback(async ({ label, start, end, isAuthenticated, accessToken, validatorId }: SubmitArgs) => {
    if (!clip) {
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const payload: Record<string, unknown> = {
        id: clip.id,
        label,
      };

      if (typeof start === "number" && typeof end === "number" && start !== end) {
        payload.start = start;
        payload.end = end;
      }

      if (stage === "validate" && validatorId) {
        payload.validator_id = validatorId;
      }

      const endpoint = isAuthenticated ? STAGE_CONFIG[stage].submitPath.authenticated : STAGE_CONFIG[stage].submitPath.anonymous;
      const headers = isAuthenticated && accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined;
      await axios.put(`${API_BASE}${endpoint}`, payload, { headers });
      await fetchNextClip(false);
    } catch (err) {
      console.error(`Failed to submit ${stage} audio`, err);
      setError(copy.submitError ?? "Submission failed. Please try again.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clip, copy.submitError, stage, fetchNextClip]);

  const deleteClipHandler = useCallback(async () => {
    if (!clip) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      await axios.delete(`${API_BASE}audio`, { data: { id: clip.id } });
      await fetchNextClip(false);
    } catch (err) {
      console.error("Failed to delete audio", err);
      setError(copy.deleteError ?? "Unable to delete audio right now.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clip, copy.deleteError, fetchNextClip]);

  const deleteClip = STAGE_CONFIG[stage].allowDelete ? deleteClipHandler : undefined;

  return {
    clip,
    isLoading,
    statusMessage,
    error,
    fetchNextClip,
    submitClip,
    deleteClip,
  };
}
