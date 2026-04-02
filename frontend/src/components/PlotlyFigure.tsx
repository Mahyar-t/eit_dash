import { type CSSProperties, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

type PlotlyFigureProps = {
  figure: Record<string, unknown> | null;
  className?: string;
  style?: CSSProperties;
  onRelayout?: (payload: Record<string, unknown>) => void;
  onGraphReady?: (graph: PlotlyGraphDiv | null) => void;
};

export type PlotlyGraphDiv = HTMLDivElement & {
  on: (eventName: string, handler: (payload: Record<string, unknown>) => void) => void;
  removeAllListeners?: (eventName?: string) => void;
  _transitionData?: { _frames?: unknown[] };
};

export function PlotlyFigure({ figure, className, style, onRelayout, onGraphReady }: PlotlyFigureProps) {
  const graphRef = useRef<PlotlyGraphDiv | null>(null);

  useEffect(() => {
    if (!graphRef.current || !figure) {
      return;
    }

    const graph = graphRef.current;
    const data = (figure.data as unknown[]) ?? [];
    const layout = (figure.layout as Record<string, unknown>) ?? {};
    const frames = (figure.frames as unknown[]) ?? [];
    const config = {
      responsive: true,
      displaylogo: false,
    };

    Plotly.react(graph, data, layout, config)
      .then(async () => {
        const existingFrameCount = graph._transitionData?._frames?.length ?? 0;
        if (existingFrameCount > 0 && typeof Plotly.deleteFrames === 'function') {
          await Plotly.deleteFrames(
            graph,
            Array.from({ length: existingFrameCount }, (_, index) => index),
          );
        }

        if (frames.length && typeof Plotly.addFrames === 'function') {
          await Plotly.addFrames(graph, frames);
        }

        onGraphReady?.(graph);
      })
      .catch(() => undefined);

    const handleRelayout = (payload: Record<string, unknown>) => {
      onRelayout?.(payload);
    };

    graph.on('plotly_relayout', handleRelayout);

    return () => {
      graph.removeAllListeners?.('plotly_relayout');
      onGraphReady?.(null);
    };
  }, [figure, onGraphReady, onRelayout]);

  useEffect(
    () => () => {
      if (graphRef.current) {
        Plotly.purge(graphRef.current);
      }
    },
    [],
  );

  return <div ref={graphRef} className={className} style={style} />;
}
