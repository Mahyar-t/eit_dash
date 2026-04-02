import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AnalyzePlaybackFigure } from "../components/AnalyzePlaybackFigure";
import { InfoCard } from "../components/InfoCard";
import { PlotlyFigure } from "../components/PlotlyFigure";
import { useSession } from "../hooks/useSession";
import type {
  AnalyzeAlert,
  AnalyzeCalculationResponse,
  AnalyzeCard,
  AnalyzeFigure,
  AnalyzeResultsPayload,
  AnalyzeStateResponse,
} from "../types/analyze";
import type { DatasetCard } from "../types/load";

export function AnalyzePage() {
  const { session, isLoading, error } = useSession();

  const [summaryCards, setSummaryCards] = useState<DatasetCard[]>([]);
  const [periodOptions, setPeriodOptions] = useState<
    AnalyzeStateResponse["period_options"]
  >([]);
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [canCalculate, setCanCalculate] = useState(false);
  const [results, setResults] = useState<AnalyzeResultsPayload | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [alert, setAlert] = useState<AnalyzeAlert | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  const loadResults = useCallback(
    async (periodIndex: number) => {
      if (!session) {
        return;
      }

      const response = await fetch(
        `/api/sessions/${session.session_id}/analyze/results?period_index=${periodIndex}`,
      );
      if (!response.ok) {
        throw new Error(`Analyze results fetch failed with ${response.status}`);
      }

      const payload = (await response.json()) as AnalyzeResultsPayload;
      setResults(payload);
    },
    [session],
  );

  const loadState = useCallback(async () => {
    if (!session) {
      return;
    }

    const response = await fetch(
      `/api/sessions/${session.session_id}/analyze/state`,
    );
    if (!response.ok) {
      throw new Error(`Analyze state fetch failed with ${response.status}`);
    }

    const payload = (await response.json()) as AnalyzeStateResponse;
    setSummaryCards(payload.summary_cards);
    setPeriodOptions(payload.period_options);
    setCanCalculate(payload.can_calculate);
    setSelectedPeriod((current) => {
      if (
        current !== null &&
        payload.period_options.some((option) => option.value === current)
      ) {
        return current;
      }
      return payload.selected_period;
    });

    if (payload.has_results && payload.selected_period !== null) {
      await loadResults(payload.selected_period);
    } else {
      setResults(null);
    }
  }, [loadResults, session]);

  useEffect(() => {
    loadState().catch((caughtError: unknown) => {
      setPageError(
        caughtError instanceof Error
          ? caughtError.message
          : "Analyze state fetch failed.",
      );
    });
  }, [loadState]);

  const handleCalculate = useCallback(async () => {
    if (!session) {
      return;
    }

    setIsCalculating(true);
    setPageError(null);

    try {
      const response = await fetch(
        `/api/sessions/${session.session_id}/analyze/calculate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ selected_period: selectedPeriod }),
        },
      );

      if (!response.ok) {
        throw new Error(`Analyze calculation failed with ${response.status}`);
      }

      const payload = (await response.json()) as AnalyzeCalculationResponse;
      setAlert(payload.alert);
      setResults(payload.results);
    } catch (caughtError: unknown) {
      setAlert({
        is_open: true,
        message:
          caughtError instanceof Error
            ? caughtError.message
            : "Analyze calculation failed.",
        color: "danger",
      });
    } finally {
      setIsCalculating(false);
    }
  }, [selectedPeriod, session]);

  const handlePeriodChange = useCallback(
    (nextPeriod: number) => {
      setSelectedPeriod(nextPeriod);
      if (results) {
        loadResults(nextPeriod).catch((caughtError: unknown) => {
          setPageError(
            caughtError instanceof Error
              ? caughtError.message
              : "Could not load the selected period results.",
          );
        });
      }
    },
    [loadResults, results],
  );

  return (
    <div className="page-shell">
      <div className="stage-card glass-panel">
        <div className="page-hero">
          <p className="page-kicker">Analyze Data</p>
          <p className="page-intro">
            Review the saved periods, launch the analysis, and inspect the
            output.
          </p>
        </div>

        <div className="workflow-board">
          <section className="workflow-section workflow-section--feature workflow-section--summary">
            <h2 className="section-heading">Summary</h2>
            <div className="glass-panel--results card-stack analyze-summary-stack">
              {summaryCards.map((card) => (
                <InfoCard key={card.label} card={card} />
              ))}
              {!summaryCards.length ? (
                <p className="field-meta">
                  Load datasets in Step 1 and save periods in Step 2 to begin
                  the analysis.
                </p>
              ) : null}
            </div>
          </section>

          <section className="workflow-section workflow-section--feature">
            <h2 className="section-heading">Selecting the period</h2>
            <p className="panel-copy analyze-panel-copy">
              Run the analysis on the selected stable period and review the
              resulting metrics, plots, and EIT outputs.
            </p>

            <p className="panel-copy analyze-panel-copy">
              Select a period and press "Calculate results" to analyze
            </p>
            <div className="form-row form-row--wide">
              <div className="field-grow">
                <select
                  className="form-select"
                  value={selectedPeriod ?? ""}
                  disabled={!periodOptions.length || isLoading}
                  onChange={(event) =>
                    handlePeriodChange(Number(event.target.value))
                  }
                >
                  {!periodOptions.length ? (
                    <option value="">No saved periods</option>
                  ) : null}
                  {periodOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                className="glass-button glass-button--primary button-stretch"
                disabled={!canCalculate || isLoading || isCalculating}
                onClick={() => {
                  handleCalculate().catch(() => undefined);
                }}
              >
                {isCalculating ? "Calculating..." : "Calculate results"}
              </button>
            </div>

            {alert?.is_open && alert.message ? (
              <div
                className={`analyze-alert analyze-alert--${alert.color ?? "neutral"}`}
              >
                {alert.message}
              </div>
            ) : null}
            {error || pageError ? (
              <p className="field-meta analyze-inline-error">
                {error || pageError}
              </p>
            ) : null}
          </section>

          <section className="workflow-section workflow-section--feature workflow-section--results">
            <h2 className="section-heading">Results</h2>
            <div className="glass-panel--results analyze-results-panel">
              {results ? (
                <div className="analyze-results-stack">
                  <AnalyzeCardView
                    card={results.overview}
                    sessionId={session?.session_id ?? ""}
                    onError={setPageError}
                  />

                  <div className="analyze-accordion-stack">
                    {results.sections.map((section) => (
                      <details
                        key={section.title}
                        className="analyze-accordion"
                        open
                      >
                        <summary className="analyze-accordion__summary">
                          {section.title}
                        </summary>
                        <div className="analyze-accordion__body">
                          {section.items.length ? (
                            section.items.map((card) => (
                              <AnalyzeCardView
                                key={`${section.title}-${card.title}`}
                                card={card}
                                sessionId={session?.session_id ?? ""}
                                onError={setPageError}
                              />
                            ))
                          ) : (
                            <p className="field-meta">
                              {section.empty_message}
                            </p>
                          )}
                        </div>
                      </details>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="field-meta analyze-empty-results">
                  {periodOptions.length
                    ? "Calculate results to inspect the selected period."
                    : "Save stable periods in Step 2 to unlock the analysis workflow."}
                </p>
              )}
            </div>
          </section>
        </div>

        <div className="process-footer">
          <Link
            to="/preprocessing"
            className="process-nav-button process-nav-button--back"
          >
            <span>&lt;</span>
            <span>Back</span>
          </Link>
          <div className="process-footer-spacer" />
        </div>
      </div>
    </div>
  );
}

type AnalyzeCardViewProps = {
  card: AnalyzeCard;
  sessionId: string;
  onError: (message: string | null) => void;
};

function AnalyzeCardView({ card, sessionId, onError }: AnalyzeCardViewProps) {
  return (
    <article className="glass-card analyze-card">
      <div className="info-card__body">
        <h4 className="card-title">{card.title}</h4>

        {card.tables.map((table, tableIndex) => (
          <table
            key={`${card.title}-table-${tableIndex}`}
            className="info-table analyze-table"
          >
            <tbody>
              {table.map((row) => (
                <tr
                  key={`${card.title}-${tableIndex}-${row.label}-${row.value}`}
                >
                  <td className="info-table__label">{row.label}</td>
                  <td className="info-table__value">{row.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}

        {card.figures.map((figure, figureIndex) => (
          <AnalyzeFigureView
            key={`${card.title}-figure-${figureIndex}`}
            figure={figure}
            sessionId={sessionId}
            onError={onError}
          />
        ))}
      </div>
    </article>
  );
}

type AnalyzeFigureViewProps = {
  figure: AnalyzeFigure;
  sessionId: string;
  onError: (message: string | null) => void;
};

function AnalyzeFigureView({
  figure,
  sessionId,
  onError,
}: AnalyzeFigureViewProps) {
  if (figure.role === "eit-playback") {
    return (
      <AnalyzePlaybackFigure
        sessionId={sessionId}
        figure={figure}
        onError={onError}
      />
    );
  }

  return (
    <PlotlyFigure
      figure={figure.figure}
      className="analyze-plot"
      style={figure.height_px ? { height: `${figure.height_px}px` } : undefined}
    />
  );
}
