import { useRef, useState } from "react";

export interface VoiceRecorder {
  recording: boolean;
  blob: Blob | null;
  mimeType: string;
  start: () => Promise<void>;
  stop: () => void;
  clear: () => void;
}

export function useVoiceRecorder(): VoiceRecorder {
  const [recording, setRecording] = useState(false);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [mimeType, setMimeType] = useState("audio/webm");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const mime = recorder.mimeType || "audio/webm";
    setMimeType(mime);
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      setBlob(new Blob(chunksRef.current, { type: mime }));
      stream.getTracks().forEach((t) => t.stop());
    };

    recorder.start();
    recorderRef.current = recorder;
    setRecording(true);
  };

  const stop = () => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setRecording(false);
  };

  const clear = () => {
    setBlob(null);
    chunksRef.current = [];
  };

  return { recording, blob, mimeType, start, stop, clear };
}
