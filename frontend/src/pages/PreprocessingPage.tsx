import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";

import { InfoCard } from "../components/InfoCard";
import { PlotlyFigure } from "../components/PlotlyFigure";
import { useSession } from "../hooks/useSession";
import type { DatasetCard } from "../types/load";
import type {
  FilterApplyResponse,
  FilterFigureResponse,
  PeriodPreviewResponse,
  PeriodsMutationResponse,
  PreprocessingStateResponse,
} from "../types/preprocessing";

const periodMethodOptions = [{ label: "Manual", value: 0 }] as const;
const filterOptions = [
  { label: "lowpass", value: 0 },
  { label: "highpass", value: 1 },
  { label: "bandpass", value: 2 },
  { label: "bandstop", value: 3 },
] as const;

export function PreprocessingPage() {
  const { session, isLoading, error } = useSession();

  const [summaryDatasets, setSummaryDatasets] = useState<DatasetCard[]>([]);
  const [selectedPeriods, setSelectedPeriods] = useState<DatasetCard[]>([]);
  const [filterCard, setFilterCard] = useState<DatasetCard | null>(null);
  const [datasetOptions, setDatasetOptions] = useState<
    PreprocessingStateResponse["dataset_options"]
  >([]);
  const [canSelectPeriods, setCanSelectPeriods] = useState(false);
  const [canFilter, setCanFilter] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const [periodModalOpen, setPeriodModalOpen] = useState(false);
  const [filterModalOpen, setFilterModalOpen] = useState(false);

  const [periodMethod, setPeriodMethod] = useState(0);
  const [selectedDatasetIndex, setSelectedDatasetIndex] = useState<
    number | null
  >(null);
  const [periodPreview, setPeriodPreview] =
    useState<PeriodPreviewResponse | null>(null);
  const [selectedSignals, setSelectedSignals] = useState<number[]>([]);
  const [periodName, setPeriodName] = useState("");
  const [relayoutData, setRelayoutData] = useState<Record<
    string,
    unknown
  > | null>(null);

  const [filterType, setFilterType] = useState<number | null>(null);
  const [filterOrder, setFilterOrder] = useState<number>(2);
  const [cutoffLow, setCutoffLow] = useState("");
  const [cutoffHigh, setCutoffHigh] = useState("");
  const [filterAlert, setFilterAlert] = useState<string | null>(null);
  const [filterSavedAlert, setFilterSavedAlert] = useState<string | null>(null);
  const [filterPeriodOptions, setFilterPeriodOptions] = useState<
    FilterApplyResponse["period_options"]
  >([]);
  const [selectedFilterPeriod, setSelectedFilterPeriod] = useState<
    number | null
  >(null);
  const [filterFigure, setFilterFigure] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [filterConfirmEnabled, setFilterConfirmEnabled] = useState(false);

  const anyModalOpen = periodModalOpen || filterModalOpen;

  useEffect(() => {
    document.body.classList.toggle("load-modal-open", anyModalOpen);
    return () => {
      document.body.classList.remove("load-modal-open");
    };
  }, [anyModalOpen]);

  const loadState = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/preprocessing/state`,
    );
    if (!response.ok) {
      throw new Error(
        `Preprocessing state fetch failed with ${response.status}`,
      );
    }

    const payload = (await response.json()) as PreprocessingStateResponse;
    setSummaryDatasets(payload.summary_datasets);
    setDatasetOptions(payload.dataset_options);
    setSelectedPeriods(payload.selected_periods);
    setFilterCard(payload.filter_card);
    setCanSelectPeriods(payload.can_select_periods);
    setCanFilter(payload.can_filter);
    setSelectedDatasetIndex(
      (current) => current ?? payload.dataset_options[0]?.value ?? null,
    );
  }, [session]);

  useEffect(() => {
    loadState().catch((caughtError: unknown) => {
      setPageError(
        caughtError instanceof Error
          ? caughtError.message
          : "Preprocessing state fetch failed.",
      );
    });
  }, [loadState]);

  const loadPeriodPreview = useCallback(
    async (datasetIndex: number, nextSelectedSignals?: number[]) => {
      if (!session) {
        return;
      }

      const response = await fetch(
        `/api/sessions/${session.session_id}/preprocessing/periods/preview`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dataset_index: datasetIndex,
            selected_signals: nextSelectedSignals,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Period preview failed with ${response.status}`);
      }

      const payload = (await response.json()) as PeriodPreviewResponse;
      setPeriodPreview(payload);
      setSelectedSignals(payload.selected_signals);
      setSelectedDatasetIndex(payload.dataset_index);
      setRelayoutData(null);
    },
    [session],
  );

  const openPeriodModal = useCallback(() => {
    if (selectedDatasetIndex === null) {
      return;
    }

    setPageError(null);
    setPeriodName("");
    setRelayoutData(null);
    setPeriodModalOpen(true);
    loadPeriodPreview(selectedDatasetIndex).catch((caughtError: unknown) => {
      setPageError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not load period preview.",
      );
    });
  }, [loadPeriodPreview, selectedDatasetIndex]);

  const handleSignalToggle = useCallback(
    (value: number) => {
      if (selectedDatasetIndex === null) {
        return;
      }

      const nextSignals = selectedSignals.includes(value)
        ? selectedSignals.filter((signal) => signal !== value)
        : [...selectedSignals, value];

      loadPeriodPreview(selectedDatasetIndex, nextSignals).catch(
        (caughtError: unknown) => {
          setPageError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not update preview signals.",
          );
        },
      );
    },
    [loadPeriodPreview, selectedDatasetIndex, selectedSignals],
  );

  const applySelectedPeriod = useCallback(async () => {
    if (!session || selectedDatasetIndex === null) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/preprocessing/periods`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_index: selectedDatasetIndex,
          relayout_data: relayoutData,
          selected_signals: selectedSignals,
          custom_name: periodName || null,
        }),
      },
    );

    if (!response.ok) {
      throw new Error(`Could not save selected period (${response.status}).`);
    }

    const payload = (await response.json()) as PeriodsMutationResponse;
    setSelectedPeriods(payload.selected_periods);
    setCanFilter(Boolean(payload.can_filter));
    setPeriodName("");
    if (payload.period_preview) {
      setPeriodPreview(payload.period_preview);
      setSelectedSignals(payload.period_preview.selected_signals);
      setRelayoutData(null);
    } else {
      await loadPeriodPreview(selectedDatasetIndex, selectedSignals);
    }
  }, [
    loadPeriodPreview,
    periodName,
    relayoutData,
    selectedDatasetIndex,
    selectedSignals,
    session,
  ]);

  const removePeriod = useCallback(
    async (label: string) => {
      if (!session) {
        return;
      }

      const response = await fetch(
        `/api/sessions/${session.session_id}/preprocessing/periods/${encodeURIComponent(label)}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as PeriodsMutationResponse;
      setSelectedPeriods(payload.selected_periods);
      setFilterCard(payload.filter_card);
      setCanFilter(Boolean(payload.can_filter));

      if (periodModalOpen && selectedDatasetIndex !== null) {
        loadPeriodPreview(selectedDatasetIndex).catch(() => undefined);
      }
    },
    [loadPeriodPreview, periodModalOpen, selectedDatasetIndex, session],
  );

  const openFilterModal = useCallback(() => {
    setFilterModalOpen(true);
    setFilterType(null);
    setFilterOrder(2);
    setCutoffLow("");
    setCutoffHigh("");
    setFilterAlert(null);
    setFilterSavedAlert(null);
    setFilterPeriodOptions([]);
    setSelectedFilterPeriod(null);
    setFilterFigure(null);
    setFilterConfirmEnabled(false);
  }, []);

  const applyFilter = useCallback(async () => {
    if (!session || filterType === null) {
      return;
    }

    setFilterAlert(null);
    setFilterSavedAlert(null);
    const response = await fetch(
      `/api/sessions/${session.session_id}/preprocessing/filter/apply`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filter_type: filterType,
          cutoff_low: cutoffLow === "" ? null : Number(cutoffLow),
          cutoff_high: cutoffHigh === "" ? null : Number(cutoffHigh),
          order: filterOrder,
        }),
      },
    );

    if (!response.ok) {
      setFilterAlert(`Could not apply filter (${response.status}).`);
      return;
    }

    const payload = (await response.json()) as FilterApplyResponse;
    setFilterPeriodOptions(payload.period_options);
    setFilterConfirmEnabled(payload.confirm_enabled);

    const firstPeriod = payload.period_options[0]?.value ?? null;
    setSelectedFilterPeriod(firstPeriod);
    if (firstPeriod !== null) {
      const previewResponse = await fetch(
        `/api/sessions/${session.session_id}/preprocessing/filter/preview/${firstPeriod}`,
      );
      if (previewResponse.ok) {
        const previewPayload =
          (await previewResponse.json()) as FilterFigureResponse;
        setFilterFigure(previewPayload.figure);
      }
    }
  }, [cutoffHigh, cutoffLow, filterOrder, filterType, session]);

  const loadFilteredPreview = useCallback(
    async (periodIndex: number) => {
      if (!session) {
        return;
      }

      const response = await fetch(
        `/api/sessions/${session.session_id}/preprocessing/filter/preview/${periodIndex}`,
      );
      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as FilterFigureResponse;
      setFilterFigure(payload.figure);
    },
    [session],
  );

  const confirmFilter = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/preprocessing/filter/confirm`,
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      return;
    }

    const payload = (await response.json()) as PeriodsMutationResponse;
    setSelectedPeriods(payload.selected_periods);
    setFilterCard(payload.filter_card);
    setFilterSavedAlert("Results have been saved");
  }, [session]);

  const removeFilter = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/preprocessing/filter`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) {
      return;
    }

    const payload = (await response.json()) as PeriodsMutationResponse;
    setSelectedPeriods(payload.selected_periods);
    setFilterCard(payload.filter_card);
    setFilterPeriodOptions([]);
    setSelectedFilterPeriod(null);
    setFilterFigure(null);
    setFilterConfirmEnabled(false);
    setFilterSavedAlert(null);
  }, [session]);

  const filterControlsDisabled = useMemo(() => {
    if (filterType === null || filterOrder <= 0) {
      return true;
    }

    if (filterType === 0) {
      return cutoffHigh === "";
    }
    if (filterType === 1) {
      return cutoffLow === "";
    }

    return cutoffLow === "" || cutoffHigh === "";
  }, [cutoffHigh, cutoffLow, filterOrder, filterType]);

  return (
    <div className="page-shell">
      <div className="stage-card glass-panel">
        <div className="page-hero">
          <p className="page-kicker">Pre-processing steps</p>
          <p className="page-intro">
            Select stable periods, preview the treatment on top of the raw
            signal, and confirm only the preprocessing results you trust.
          </p>
        </div>

        <div className="workflow-board">
          <section className="workflow-section workflow-section--feature workflow-section--summary">
            <h2 className="section-heading">Summary</h2>
            <div className="glass-panel--results card-stack preprocessing-summary-stack">
              {summaryDatasets.map((dataset) => (
                <InfoCard key={dataset.label} card={dataset} />
              ))}
              {!summaryDatasets.length ? (
                <p className="field-meta">
                  Load datasets in step 1 to begin preprocessing.
                </p>
              ) : null}
            </div>
          </section>

          <section className="workflow-section workflow-section--feature">
            <h2 className="section-heading">Pre-process data</h2>
            <p className="panel-copy preprocessing-panel-copy">
              Select stable periods, confirm the segments you want to use in the
              analysis step and apply filters to the raw signals.
            </p>

            <div className="button-grid preprocessing-action-grid">
              <button
                type="button"
                className="glass-button glass-button--primary"
                disabled={!canSelectPeriods || isLoading}
                onClick={openPeriodModal}
              >
                Select periods
              </button>
              <button
                type="button"
                className="glass-button glass-button--secondary"
                disabled={!canFilter || isLoading}
                onClick={openFilterModal}
              >
                Filter data
              </button>
            </div>

            {error || pageError ? (
              <p className="field-meta preprocessing-inline-error">
                {error || pageError}
              </p>
            ) : null}
          </section>

          <section className="workflow-section workflow-section--feature workflow-section--results">
            <h2 className="section-heading">Selected periods</h2>
            <div className="glass-panel--results card-stack preprocessing-results-stack">
              {selectedPeriods.map((period) => (
                <InfoCard
                  key={period.label}
                  card={period}
                  onRemove={removePeriod}
                />
              ))}
              {filterCard ? (
                <InfoCard card={filterCard} onRemove={removeFilter} />
              ) : null}
              {!selectedPeriods.length && !filterCard ? (
                <p className="field-meta">No periods have been saved yet.</p>
              ) : null}
            </div>
          </section>
        </div>

        <div className="process-footer">
          <Link
            to="/load"
            className="process-nav-button process-nav-button--back"
          >
            <span>&lt;</span>
            <span>Back</span>
          </Link>
          <Link
            to="/analyze"
            className="process-nav-button process-nav-button--next"
          >
            <span>Next</span>
            <span>&gt;</span>
          </Link>
        </div>
      </div>

      {periodModalOpen
        ? createPortal(
            <div
              className="modal-shell"
              role="dialog"
              aria-modal="true"
              aria-labelledby="period-title"
            >
              <div className="modal-content glass-modal preprocessing-modal preprocessing-modal--wide preprocessing-period-modal">
                <div className="modal-header">
                  <h3 id="period-title">Periods selection</h3>
                  <button
                    type="button"
                    className="modal-close"
                    onClick={() => setPeriodModalOpen(false)}
                  >
                    ×
                  </button>
                </div>
                <div className="modal-body card-stack">
                  <div>
                    <h3 className="panel-title">Periods selection method</h3>
                    <select
                      className="form-select"
                      value={periodMethod}
                      onChange={(event) =>
                        setPeriodMethod(Number(event.target.value))
                      }
                    >
                      {periodMethodOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <h3 className="panel-title">Select one dataset</h3>
                    <select
                      className="form-select"
                      value={selectedDatasetIndex ?? ""}
                      onChange={(event) => {
                        const nextIndex = Number(event.target.value);
                        setSelectedDatasetIndex(nextIndex);
                        loadPeriodPreview(nextIndex).catch(
                          (caughtError: unknown) => {
                            setPageError(
                              caughtError instanceof Error
                                ? caughtError.message
                                : "Could not load dataset preview.",
                            );
                          },
                        );
                      }}
                    >
                      {datasetOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {periodPreview ? (
                    <>
                      <div>
                        <h3 className="panel-title">
                          Select the signals to be displayed
                        </h3>
                        <div className="signal-checklist">
                          {periodPreview.options.map((signal) => (
                            <label key={signal.value} className="check-pill">
                              <input
                                type="checkbox"
                                checked={selectedSignals.includes(signal.value)}
                                onChange={() =>
                                  handleSignalToggle(signal.value)
                                }
                              />
                              <span>{signal.label}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div className="preprocessing-period-preview">
                        <PlotlyFigure
                          className="dash-graph"
                          figure={periodPreview.figure}
                          onRelayout={(payload) => setRelayoutData(payload)}
                        />
                      </div>

                      <div>
                        <h3 className="panel-title preprocessing-period-name">
                          Period name
                        </h3>
                        <input
                          className="form-control glass-input"
                          placeholder="Enter period name (optional)..."
                          value={periodName}
                          onChange={(event) =>
                            setPeriodName(event.target.value)
                          }
                        />
                      </div>
                    </>
                  ) : (
                    <p className="field-meta">
                      Choose a dataset to preview and save stable periods.
                    </p>
                  )}
                </div>
                <div className="preprocessing-modal-footer">
                  <button
                    type="button"
                    className="glass-button glass-button--secondary"
                    onClick={() => {
                      applySelectedPeriod().catch((caughtError: unknown) => {
                        setPageError(
                          caughtError instanceof Error
                            ? caughtError.message
                            : "Could not save period.",
                        );
                      });
                    }}
                  >
                    Add selection
                  </button>
                  <button
                    type="button"
                    className="glass-button glass-button--primary"
                    onClick={() => setPeriodModalOpen(false)}
                  >
                    Confirm
                  </button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}

      {filterModalOpen
        ? createPortal(
            <div
              className="modal-shell"
              role="dialog"
              aria-modal="true"
              aria-labelledby="filter-title"
            >
              <div className="modal-content glass-modal preprocessing-modal preprocessing-modal--wide">
                <div className="modal-header">
                  <h3 id="filter-title">Filtering data</h3>
                  <button
                    type="button"
                    className="modal-close"
                    onClick={() => setFilterModalOpen(false)}
                  >
                    ×
                  </button>
                </div>
                <div className="modal-body card-stack">
                  {filterSavedAlert ? (
                    <div className="alert alert--primary">
                      {filterSavedAlert}
                    </div>
                  ) : null}
                  {filterAlert ? (
                    <div className="alert">{filterAlert}</div>
                  ) : null}

                  <div>
                    <h3 className="panel-title">Select a filter</h3>
                    <select
                      className="form-select"
                      value={filterType ?? ""}
                      onChange={(event) => {
                        const nextValue =
                          event.target.value === ""
                            ? null
                            : Number(event.target.value);
                        setFilterType(nextValue);
                        setFilterSavedAlert(null);
                        setFilterAlert(null);
                        setFilterPeriodOptions([]);
                        setSelectedFilterPeriod(null);
                        setFilterFigure(null);
                      }}
                    >
                      <option value="">Choose a filter</option>
                      {filterOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {filterType !== null ? (
                    <>
                      <div className="preprocessing-filter-grid">
                        <div>
                          <p className="label-row">Filter Order</p>
                          <input
                            className="form-control"
                            type="number"
                            min={1}
                            value={filterOrder}
                            onChange={(event) =>
                              setFilterOrder(Number(event.target.value))
                            }
                          />
                        </div>
                        <div>
                          <p className="label-row">Cut off frequency low</p>
                          <input
                            className="form-control"
                            type="number"
                            min={0}
                            disabled={filterType === 0}
                            value={cutoffLow}
                            onChange={(event) =>
                              setCutoffLow(event.target.value)
                            }
                          />
                        </div>
                        <div>
                          <p className="label-row">Cut off frequency high</p>
                          <input
                            className="form-control"
                            type="number"
                            min={0}
                            disabled={filterType === 1}
                            value={cutoffHigh}
                            onChange={(event) =>
                              setCutoffHigh(event.target.value)
                            }
                          />
                        </div>
                      </div>

                      <button
                        type="button"
                        className="glass-button glass-button--primary preprocessing-filter-apply"
                        disabled={filterControlsDisabled}
                        onClick={() => {
                          applyFilter().catch((caughtError: unknown) => {
                            setFilterAlert(
                              caughtError instanceof Error
                                ? caughtError.message
                                : "Could not apply filter.",
                            );
                          });
                        }}
                      >
                        Apply
                      </button>

                      {filterPeriodOptions.length ? (
                        <div className="card-stack">
                          <div>
                            <h3 className="panel-title">
                              Select a period to view the results
                            </h3>
                            <select
                              className="form-select"
                              value={selectedFilterPeriod ?? ""}
                              onChange={(event) => {
                                const nextPeriod = Number(event.target.value);
                                setSelectedFilterPeriod(nextPeriod);
                                loadFilteredPreview(nextPeriod).catch(
                                  () => undefined,
                                );
                              }}
                            >
                              {filterPeriodOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          {filterFigure ? (
                            <PlotlyFigure
                              className="dash-graph"
                              figure={filterFigure}
                            />
                          ) : null}
                          <div className="preprocessing-filter-confirm-row">
                            <button
                              type="button"
                              className="glass-button glass-button--primary preprocessing-filter-apply"
                              disabled={!filterConfirmEnabled}
                              onClick={() => {
                                confirmFilter().catch(
                                  (caughtError: unknown) => {
                                    setFilterAlert(
                                      caughtError instanceof Error
                                        ? caughtError.message
                                        : "Could not save filter results.",
                                    );
                                  },
                                );
                              }}
                            >
                              Confirm
                            </button>
                          </div>
                        </div>
                      ) : null}
                    </>
                  ) : null}
                </div>
                <div className="preprocessing-modal-footer">
                  <button
                    type="button"
                    className="glass-button glass-button--ghost"
                    onClick={() => setFilterModalOpen(false)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
