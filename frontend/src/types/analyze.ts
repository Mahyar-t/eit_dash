import type { DatasetCard } from './load';

export type AnalyzeAlert = {
  is_open: boolean;
  message: string | null;
  color: string | null;
};

export type AnalyzePeriodOption = {
  label: string;
  value: number;
};

export type AnalyzeFigure = {
  role: string;
  figure: Record<string, unknown>;
  playback?: {
    period_index: number;
    label: string;
    frame_count: number;
    max_frame_count: number;
  } | null;
  height_px?: number | null;
};

export type AnalyzeCard = {
  title: string;
  tables: Array<Array<{ label: string; value: string }>>;
  figures: AnalyzeFigure[];
};

export type AnalyzeSection = {
  title: string;
  items: AnalyzeCard[];
  empty_message?: string | null;
};

export type AnalyzeResultsPayload = {
  period_index: number;
  overview: AnalyzeCard;
  sections: AnalyzeSection[];
};

export type AnalyzeStateResponse = {
  summary_cards: DatasetCard[];
  period_options: AnalyzePeriodOption[];
  selected_period: number | null;
  can_calculate: boolean;
  has_results: boolean;
};

export type AnalyzeCalculationResponse = {
  alert: AnalyzeAlert;
  results: AnalyzeResultsPayload | null;
};

export type AnalyzeFramePreviewResponse = {
  figure: Record<string, unknown>;
  frame_count: number;
  max_frame_count: number;
};
