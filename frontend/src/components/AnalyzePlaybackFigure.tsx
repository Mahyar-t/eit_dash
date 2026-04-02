import { useCallback, useEffect, useMemo, useState } from 'react';
import Plotly from 'plotly.js-dist-min';

import { PlotlyFigure, type PlotlyGraphDiv } from './PlotlyFigure';
import type { AnalyzeFigure, AnalyzeFramePreviewResponse } from '../types/analyze';

type AnalyzePlaybackFigureProps = {
  sessionId: string;
  figure: AnalyzeFigure;
  onError?: (message: string | null) => void;
};

const PLAY_LABEL = '▶️ Play';
const PAUSE_LABEL = '⏸️ Pause';

export function AnalyzePlaybackFigure({ sessionId, figure, onError }: AnalyzePlaybackFigureProps) {
  const [graph, setGraph] = useState<PlotlyGraphDiv | null>(null);
  const [currentFigure, setCurrentFigure] = useState<Record<string, unknown>>(figure.figure);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playLabel, setPlayLabel] = useState(PLAY_LABEL);
  const [frameInput, setFrameInput] = useState(String(figure.playback?.frame_count ?? ''));
  const [isUpdatingFrameCount, setIsUpdatingFrameCount] = useState(false);

  const playback = useMemo(() => figure.playback ?? null, [figure.playback]);

  useEffect(() => {
    setCurrentFigure(figure.figure);
    setIsPlaying(false);
    setPlayLabel(PLAY_LABEL);
    setFrameInput(String(figure.playback?.frame_count ?? ''));
  }, [figure.figure, figure.playback]);

  const stopAnimation = useCallback(() => {
    if (!graph) {
      return;
    }

    Plotly.animate(graph, [], {
      frame: { duration: 0, redraw: false },
      mode: 'immediate',
      transition: { duration: 0 },
    }).catch(() => undefined);
  }, [graph]);

  const resetAnimation = useCallback(() => {
    if (!graph) {
      return;
    }

    stopAnimation();
    Plotly.animate(graph, ['frame-0'], {
      frame: { duration: 0, redraw: true },
      mode: 'immediate',
      transition: { duration: 0 },
    }).catch(() => undefined);
  }, [graph, stopAnimation]);

  const handlePlayPause = useCallback(() => {
    if (!graph) {
      return;
    }

    const nextIsPlaying = !isPlaying;
    if (nextIsPlaying) {
      Plotly.animate(graph, null, {
        frame: { duration: 80, redraw: true },
        fromcurrent: true,
        transition: { duration: 0 },
      }).catch(() => undefined);
      setPlayLabel(PAUSE_LABEL);
    } else {
      stopAnimation();
      setPlayLabel(PLAY_LABEL);
    }

    setIsPlaying(nextIsPlaying);
  }, [graph, isPlaying, stopAnimation]);

  const handleReset = useCallback(() => {
    setIsPlaying(false);
    setPlayLabel(PLAY_LABEL);
    resetAnimation();
  }, [resetAnimation]);

  const syncFrameCount = useCallback(
    async (nextValue: string) => {
      if (!playback) {
        return;
      }

      const parsedValue = Number.parseInt(nextValue, 10);
      if (!Number.isFinite(parsedValue)) {
        setFrameInput(String(playback.frame_count));
        return;
      }

      const clampedValue = Math.min(Math.max(parsedValue, 1), playback.max_frame_count);
      setIsUpdatingFrameCount(true);
      setFrameInput(String(clampedValue));
      onError?.(null);

      try {
        const response = await fetch(`/api/sessions/${sessionId}/analyze/eit-frame-preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            period_index: playback.period_index,
            label: playback.label,
            frame_count: clampedValue,
          }),
        });

        if (!response.ok) {
          throw new Error(`Could not update the frame playback figure (${response.status}).`);
        }

        const payload = (await response.json()) as AnalyzeFramePreviewResponse;
        setCurrentFigure(payload.figure);
        setFrameInput(String(payload.frame_count));
        setIsPlaying(false);
        setPlayLabel(PLAY_LABEL);
      } catch (caughtError: unknown) {
        setFrameInput(String(playback.frame_count));
        onError?.(
          caughtError instanceof Error
            ? caughtError.message
            : 'Could not update the frame playback figure.',
        );
      } finally {
        setIsUpdatingFrameCount(false);
      }
    },
    [onError, playback, sessionId],
  );

  if (!playback) {
    return <PlotlyFigure figure={currentFigure} className="analyze-plot" />;
  }

  return (
    <div className="analyze-playback-card">
      <PlotlyFigure
        figure={currentFigure}
        className="analyze-plot analyze-plot--playback"
        style={figure.height_px ? { height: `${figure.height_px}px` } : undefined}
        onGraphReady={setGraph}
      />

      <div className="analyze-playback__controls">
        <button type="button" className="playback-btn playback-btn--primary" onClick={handlePlayPause}>
          {playLabel}
        </button>
        <button type="button" className="playback-btn playback-btn--secondary" onClick={handleReset}>
          ⏮️ Reset
        </button>
      </div>

      <div className="analyze-frame-control">
        <span className="analyze-frame-control__label">Frames to show</span>
        <input
          type="number"
          min={1}
          max={playback.max_frame_count}
          step={1}
          className="analyze-frame-control__input"
          value={frameInput}
          disabled={isUpdatingFrameCount}
          onChange={(event) => setFrameInput(event.target.value)}
          onBlur={(event) => {
            syncFrameCount(event.target.value).catch(() => undefined);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              syncFrameCount(frameInput).catch(() => undefined);
            }
          }}
        />
      </div>
    </div>
  );
}
