import type { DatasetCard } from './load';

export type DatasetOption = {
  label: string;
  value: number;
};

export type PreprocessingStateResponse = {
  summary_datasets: DatasetCard[];
  dataset_options: DatasetOption[];
  selected_periods: DatasetCard[];
  filter_card: DatasetCard | null;
  can_select_periods: boolean;
  can_filter: boolean;
};

export type PeriodPreviewResponse = {
  dataset_index: number;
  options: Array<{ label: string; value: number }>;
  selected_signals: number[];
  figure: Record<string, unknown>;
};

export type PeriodsMutationResponse = {
  selected_periods: DatasetCard[];
  filter_card: DatasetCard | null;
  can_filter?: boolean | null;
  period_preview?: PeriodPreviewResponse | null;
};

export type FilterApplyResponse = {
  period_options: DatasetOption[];
  confirm_enabled: boolean;
};

export type FilterFigureResponse = {
  figure: Record<string, unknown>;
};
