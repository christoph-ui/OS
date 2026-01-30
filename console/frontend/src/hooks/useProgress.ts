import { useState, useEffect, useCallback } from 'react';

interface ProgressUpdate {
  type: 'upload' | 'ingestion' | 'deployment' | 'connected' | 'ping';
  progress?: number;
  message?: string;
  phase?: string;
  explanation?: string;
  files_processed?: number;
  files_total?: number;
}

interface ProgressState {
  upload: ProgressUpdate | null;
  ingestion: ProgressUpdate | null;
  deployment: ProgressUpdate | null;
}

export function useProgress(customerId: string) {
  const [progress, setProgress] = useState<ProgressState>({
    upload: null,
    ingestion: null,
    deployment: null,
  });
  const [connected, setConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!customerId) return;

    const websocket = new WebSocket(`ws://localhost:4080/api/ws/progress/${customerId}`);

    websocket.onopen = () => {
      console.log('Progress WebSocket connected');
      setConnected(true);
    };

    websocket.onmessage = (event) => {
      const data: ProgressUpdate = JSON.parse(event.data);

      if (data.type === 'connected' || data.type === 'ping') {
        return;
      }

      setProgress(prev => ({
        ...prev,
        [data.type]: data,
      }));
    };

    websocket.onerror = (error) => {
      console.error('Progress WebSocket error:', error);
      setConnected(false);
    };

    websocket.onclose = () => {
      console.log('Progress WebSocket closed');
      setConnected(false);

      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        console.log('Reconnecting...');
        connect();
      }, 3000);
    };

    setWs(websocket);
  }, [customerId]);

  useEffect(() => {
    connect();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connect]);

  const overallProgress = () => {
    const phases = [progress.upload, progress.ingestion, progress.deployment].filter(Boolean);
    if (phases.length === 0) return 0;

    const total = phases.reduce((sum, p) => sum + (p?.progress || 0), 0);
    return Math.floor(total / 3); // Average of 3 phases
  };

  return {
    progress,
    connected,
    overallProgress: overallProgress(),
  };
}
