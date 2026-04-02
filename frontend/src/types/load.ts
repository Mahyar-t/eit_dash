export type SessionResponse = {
  session_id: string;
  label: string;
  created_at: number;
};

export type BrowserEntry = {
  name: string;
  path: string;
  is_dir: boolean;
  icon: string;
  icon_class: string;
};

export type BrowserResponse = {
  cwd: string;
  entries: BrowserEntry[];
};

export type DatasetCard = {
  label: string;
  title: string;
  rows: Array<{ label: string; value: string | number }>;
};

export type LoadStateResponse = {
  cwd: string;
  datasets: DatasetCard[];
};

export type PreviewResponse = {
  source_path: string;
  options: Array<{ label: string; value: number }>;
  selected_signals: number[];
  figure: Record<string, unknown>;
};

export type SelectPathResponse = {
  mode: 'directory' | 'invalid_file' | 'file_loaded';
  browser: BrowserResponse;
  preview: PreviewResponse | null;
  alert_open: boolean;
  alert_message: string | null;
};

export type LoadStateMutationResponse = {
  datasets: DatasetCard[];
  preview_hidden: boolean;
};
