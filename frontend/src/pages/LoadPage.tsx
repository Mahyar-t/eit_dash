import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";

import { InfoCard } from "../components/InfoCard";
import { PlotlyFigure } from "../components/PlotlyFigure";
import { useSession } from "../hooks/useSession";
import type {
  BrowserEntry,
  BrowserResponse,
  LoadStateMutationResponse,
  LoadStateResponse,
  PreviewResponse,
  SelectPathResponse,
} from "../types/load";

const vendorOptions = [
  { label: "Draeger", value: 1 },
  { label: "Sentec", value: 2 },
  { label: "Timpel", value: 0 },
] as const;

export function LoadPage() {
  const { session, isLoading, error } = useSession();
  const [vendorType, setVendorType] = useState<number>(1);
  const [browser, setBrowser] = useState<BrowserResponse | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [selectedSignals, setSelectedSignals] = useState<number[]>([]);
  const [relayoutData, setRelayoutData] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [customName, setCustomName] = useState("");
  const [datasets, setDatasets] = useState<LoadStateResponse["datasets"]>([]);
  const [isBusy, setIsBusy] = useState(false);
  const preservedScrollY = useRef<number | null>(null);

  const loadState = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/load/state`,
    );
    if (!response.ok) {
      throw new Error(`Load state fetch failed with ${response.status}`);
    }

    const payload = (await response.json()) as LoadStateResponse;
    setDatasets(payload.datasets);
    setBrowser((current) =>
      current
        ? { ...current, cwd: payload.cwd }
        : { cwd: payload.cwd, entries: [] },
    );
  }, [session]);

  useEffect(() => {
    loadState().catch((caughtError: unknown) => {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "Load state fetch failed.";
      setAlertMessage(message);
    });
  }, [loadState]);

  useEffect(() => {
    document.body.classList.toggle("load-modal-open", modalOpen);
    return () => {
      document.body.classList.remove("load-modal-open");
    };
  }, [modalOpen]);

  useLayoutEffect(() => {
    if (preservedScrollY.current === null) {
      return;
    }

    window.scrollTo({ top: preservedScrollY.current, behavior: "auto" });
    preservedScrollY.current = null;
  }, [preview]);

  const openBrowser = useCallback(async () => {
    if (!session) {
      return;
    }

    setModalOpen(true);
    setAlertMessage(null);
    setIsBusy(true);

    try {
      const response = await fetch(
        `/api/sessions/${session.session_id}/load/open`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ vendor_type: vendorType }),
        },
      );

      if (!response.ok) {
        throw new Error(
          `Could not open the file browser (${response.status}).`,
        );
      }

      const payload = (await response.json()) as BrowserResponse;
      setBrowser(payload);
      setAlertMessage(null);
    } catch (caughtError: unknown) {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "Could not open the file browser. Make sure the API is running.";
      setAlertMessage(message);
    } finally {
      setIsBusy(false);
    }
  }, [session, vendorType]);

  const handlePathSelection = useCallback(
    async (path: string, vendorTypeOverride?: number) => {
      if (!session) {
        return;
      }

      const activeVendorType = vendorTypeOverride ?? vendorType;
      setIsBusy(true);

      try {
        const response = await fetch(
          `/api/sessions/${session.session_id}/load/select-path`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path, vendor_type: activeVendorType }),
          },
        );

        if (!response.ok) {
          throw new Error(
            `The selected file cannot be loaded (${response.status}).`,
          );
        }

        const payload = (await response.json()) as SelectPathResponse;
        setBrowser(payload.browser);
        setAlertMessage(payload.alert_open ? payload.alert_message : null);

        if (payload.mode === "directory") {
          setModalOpen(true);
          return;
        }

        if (payload.mode === "invalid_file") {
          setModalOpen(true);
          return;
        }

        if (payload.preview) {
          setPreview(payload.preview);
          setSelectedSignals(payload.preview.selected_signals);
          setRelayoutData(null);
          setCustomName("");
        }
        setModalOpen(false);
      } catch (caughtError: unknown) {
        const message =
          caughtError instanceof Error
            ? caughtError.message
            : "The selected file could not be loaded. Make sure the API is running.";
        setAlertMessage(message);
        setModalOpen(true);
      } finally {
        setIsBusy(false);
      }
    },
    [session, vendorType],
  );

  const handleParentDirectory = useCallback(() => {
    if (!browser) {
      return;
    }
    handlePathSelection(`${browser.cwd}/..`).catch(() => undefined);
  }, [browser, handlePathSelection]);

  const handleBrowserEntryClick = useCallback(
    (entry: BrowserEntry) => {
      handlePathSelection(entry.path).catch(() => undefined);
    },
    [handlePathSelection],
  );

  const updatePreview = useCallback(
    async (nextSelectedSignals: number[]) => {
      if (!session || !preview) {
        return;
      }

      preservedScrollY.current = window.scrollY;
      setSelectedSignals(nextSelectedSignals);
      const response = await fetch(
        `/api/sessions/${session.session_id}/load/preview`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ selected_signals: nextSelectedSignals }),
        },
      );

      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as PreviewResponse;
      setPreview((currentPreview) =>
        currentPreview
          ? {
              ...currentPreview,
              figure: payload.figure,
              selected_signals: payload.selected_signals,
            }
          : payload,
      );
    },
    [preview, session],
  );

  const handleSignalToggle = useCallback(
    (value: number) => {
      const nextSelectedSignals = selectedSignals.includes(value)
        ? selectedSignals.filter((signal) => signal !== value)
        : [...selectedSignals, value];
      updatePreview(nextSelectedSignals).catch(() => undefined);
    },
    [selectedSignals, updatePreview],
  );

  const handleCancel = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/load/cancel`,
      { method: "POST" },
    );
    if (!response.ok) {
      return;
    }

    const payload = (await response.json()) as LoadStateMutationResponse;
    setDatasets(payload.datasets);
    setPreview(null);
    setSelectedSignals([]);
    setRelayoutData(null);
    setCustomName("");
  }, [session]);

  const handleConfirm = useCallback(async () => {
    if (!session || !preview) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/load/confirm`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          relayout_data: relayoutData,
          selected_signals: selectedSignals,
          custom_name: customName || null,
        }),
      },
    );

    if (!response.ok) {
      return;
    }

    const payload = (await response.json()) as LoadStateMutationResponse;
    setDatasets(payload.datasets);
    setPreview(null);
    setSelectedSignals([]);
    setRelayoutData(null);
    setCustomName("");
  }, [customName, preview, relayoutData, selectedSignals, session]);

  const removeDataset = useCallback(
    async (label: string) => {
      if (!session) {
        return;
      }

      const response = await fetch(
        `/api/sessions/${session.session_id}/load/datasets/${encodeURIComponent(label)}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as LoadStateMutationResponse;
      setDatasets(payload.datasets);
    },
    [session],
  );

  return (
    <div className="page-shell page-shell--workflow">
      <div className="stage-card glass-panel">
        <div className="page-hero">
          <h2 className="page-kicker">1. Load Data</h2>
          <p className="page-intro">
            Bring in a local file, inspect the available channels, and prepare a
            clean set of datasets for the next stage. Loaded datasets and
            selections will appear here.
          </p>
        </div>

        <div className="workflow-board">
          <section className="workflow-section workflow-section--feature">
            <h2 className="section-heading">Load Datasets</h2>
            <p className="page-intro">
              Choose a vendor format, preview the recording, and cut the
              imported file into datasets you want to keep.
            </p>
            <div className="action-stack action-stack--spaced">
              <div className="form-row form-row--wide">
                <div className="field-grow">
                  <select
                    className="form-select"
                    value={vendorType}
                    onChange={(event) => {
                      const nextVendorType = Number(event.target.value);
                      setVendorType(nextVendorType);

                      if (modalOpen && browser) {
                        handlePathSelection(browser.cwd, nextVendorType).catch(
                          (caughtError: unknown) => {
                            const message =
                              caughtError instanceof Error
                                ? caughtError.message
                                : "The file browser could not be refreshed.";
                            setAlertMessage(message);
                          },
                        );
                      }
                    }}
                  >
                    {vendorOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="button"
                  className="glass-button glass-button--primary button-stretch"
                  onClick={() => {
                    openBrowser().catch((caughtError: unknown) => {
                      const message =
                        caughtError instanceof Error
                          ? caughtError.message
                          : "Could not open the file browser.";
                      setAlertMessage(message);
                    });
                  }}
                  disabled={isLoading || !session || isBusy}
                >
                  Select Files
                </button>
              </div>
              {error ? <p className="field-meta">{error}</p> : null}
            </div>
          </section>

          <section className="workflow-section workflow-section--feature workflow-section--results">
            <h2 className="section-heading">Data Preview</h2>
            <div className="glass-panel--results">
              {preview ? (
                <div className="preview-grid">
                  <div>
                    <h3 className="panel-title">Pre-selection</h3>
                    <PlotlyFigure
                      className="dash-graph"
                      figure={preview.figure}
                      onRelayout={(payload) => setRelayoutData(payload)}
                    />
                  </div>
                  <div>
                    <h3 className="panel-title">Signal selections</h3>
                    <div className="signal-checklist">
                      {preview.options.map((signal) => (
                        <label key={signal.value} className="check-pill">
                          <input
                            type="checkbox"
                            checked={selectedSignals.includes(signal.value)}
                            onChange={() => handleSignalToggle(signal.value)}
                          />
                          <span>{signal.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="panel-title">Dataset name</h3>
                    <input
                      className="form-control glass-input"
                      placeholder="Enter dataset name (optional)..."
                      value={customName}
                      onChange={(event) => setCustomName(event.target.value)}
                    />
                  </div>
                  <div className="button-grid">
                    <button
                      type="button"
                      className="glass-button glass-button--ghost"
                      onClick={() => handleCancel().catch(() => undefined)}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="glass-button glass-button--primary"
                      onClick={() => handleConfirm().catch(() => undefined)}
                    >
                      Confirm
                    </button>
                  </div>
                </div>
              ) : null}

              <div
                className={
                  preview
                    ? "dataset-container dataset-container--with-preview"
                    : "dataset-container"
                }
              >
                {datasets.map((card) => (
                  <InfoCard
                    key={card.label}
                    card={card}
                    onRemove={(label) =>
                      removeDataset(label).catch(() => undefined)
                    }
                  />
                ))}
              </div>
            </div>
          </section>
        </div>

        <div className="process-footer">
          <div className="process-footer-spacer" />
          <Link
            to="/preprocessing"
            className="process-nav-button process-nav-button--next"
          >
            <span>Next</span>
            <span>&gt;</span>
          </Link>
        </div>
      </div>

      {modalOpen
        ? createPortal(
            <div
              className="modal-shell"
              role="dialog"
              aria-modal="true"
              aria-labelledby="load-browser-title"
            >
              <div className="modal-content glass-modal">
                <div className="modal-header">
                  <h3 id="load-browser-title">Select a file</h3>
                  <button
                    type="button"
                    className="modal-close"
                    onClick={() => {
                      setModalOpen(false);
                    }}
                  >
                    ×
                  </button>
                </div>
                <div className="modal-body">
                  {alertMessage ? (
                    <div className="alert alert--primary">{alertMessage}</div>
                  ) : null}
                  <div className="browser-toolbar">
                    <button
                      type="button"
                      className="glass-button glass-button--secondary browser-parent"
                      onClick={handleParentDirectory}
                    >
                      <i
                        className="fas fa-level-up-alt browser-parent-icon"
                        aria-hidden="true"
                      />
                      <span>Parent Directory</span>
                    </button>
                  </div>
                  <div className="browser-list">
                    {isBusy && !browser?.entries.length ? (
                      <div className="field-meta">Loading files...</div>
                    ) : null}
                    {!isBusy && browser?.entries.length === 0 ? (
                      <div className="field-meta">
                        No compatible files found in this directory.
                      </div>
                    ) : null}
                    {browser?.entries.map((entry: BrowserEntry) => (
                      <button
                        key={entry.path}
                        type="button"
                        className="browser-grid-item"
                        onClick={() => handleBrowserEntryClick(entry)}
                      >
                        <span className={entry.icon_class}>{entry.icon}</span>
                        <span className="browser-item-name">{entry.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
