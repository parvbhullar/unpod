import {useCallback, useEffect, useRef, useState} from 'react';
import {useDataChannel} from '@livekit/components-react';
import {ConnectionState} from 'livekit-client';

export function useAgentMetrics(roomState) {
  const [duration, setDuration] = useState(0);
  const [turns, setTurns] = useState(0);
  const [avgLatency, setAvgLatency] = useState(0);

  const latenciesRef = useRef([]);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  // ---------------------------
  // TIMER HANDLING (CONNECTED ONLY)
  // ---------------------------

  useEffect(() => {
    if (roomState !== ConnectionState.Connected) {
      clearInterval(timerRef.current);
      timerRef.current = null;
      startTimeRef.current = null;
      setDuration(0);
      return;
    }

    startTimeRef.current = Date.now();

    timerRef.current = setInterval(() => {
      const diff = Date.now() - startTimeRef.current;
      setDuration(Math.floor(diff / 1000));
    }, 1000);

    return () => {
      clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [roomState]);

  // ---------------------------
  // DATA CHANNEL HANDLER
  // ---------------------------

  const onDataReceived = useCallback((msg) => {
    if (!msg?.payload) return;

    try {
      const payloadText = new TextDecoder().decode(msg.payload);
      const decoded = JSON.parse(payloadText);

      // Turn counter
      setTurns((prev) => prev + 1);

      // Latency calc
      if (typeof decoded.timestamp === 'number') {
        const latency = Date.now() - decoded.timestamp;

        if (latency > 0 && latency < 60000) {
          latenciesRef.current.push(latency);

          // keep last 50 values only (memory safe)
          if (latenciesRef.current.length > 50) {
            latenciesRef.current.shift();
          }

          const sum = latenciesRef.current.reduce((a, b) => a + b, 0);
          const avg = Math.round(sum / latenciesRef.current.length);

          setAvgLatency(avg);
        }
      }
    } catch (err) {
      console.warn('Metrics parse failed', err);
    }
  }, []);

  // ---------------------------
  // REGISTER DATA CHANNEL ONCE
  // ---------------------------

  useDataChannel(onDataReceived, {
    reliable: true,
  });

  // ---------------------------
  // RESET METRICS ON DISCONNECT
  // ---------------------------

  useEffect(() => {
    if (roomState === ConnectionState.Disconnected) {
      latenciesRef.current = [];
      setTurns(0);
      setAvgLatency(0);
    }
  }, [roomState]);

  return {
    duration,
    turns,
    avgLatency,
  };
}
