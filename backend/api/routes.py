from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.analyze_service import (
    build_analyze_results,
    build_analyze_state,
    build_eit_frame_preview,
    calculate_results,
)
from backend.services.load_service import (
    REPO_ROOT,
    allowed_extension_for_type,
    build_browser_payload,
    build_preview_payload,
    confirm_loaded_dataset,
    load_preview,
    serialize_loaded_datasets,
)
from backend.services.preprocessing_service import (
    add_stable_period,
    apply_filter_preview,
    build_filtered_period_preview,
    build_period_preview,
    build_preprocessing_state,
    cancel_filter_preview,
    confirm_filter_preview,
    remove_saved_filter,
    remove_stable_period,
)
from backend.state.session_store import SessionRecord, session_store

router = APIRouter(prefix='/api')


class CreateSessionRequest(BaseModel):
    label: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    label: str
    created_at: float


class BrowserEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    icon: str
    icon_class: str


class BrowserResponse(BaseModel):
    cwd: str
    entries: list[BrowserEntry]


class LoadStateResponse(BaseModel):
    cwd: str
    datasets: list[dict[str, Any]]


class OpenBrowserRequest(BaseModel):
    vendor_type: int


class SelectPathRequest(BaseModel):
    path: str
    vendor_type: int


class PreviewUpdateRequest(BaseModel):
    selected_signals: list[int] = Field(default_factory=list)


class ConfirmDatasetRequest(BaseModel):
    relayout_data: dict[str, Any] | None = None
    selected_signals: list[int] = Field(default_factory=list)
    custom_name: str | None = None


class PreviewResponse(BaseModel):
    source_path: str
    options: list[dict[str, Any]]
    selected_signals: list[int]
    figure: dict[str, Any]


class SelectPathResponse(BaseModel):
    mode: str
    browser: BrowserResponse
    preview: PreviewResponse | None = None
    alert_open: bool = False
    alert_message: str | None = None


class LoadStateMutationResponse(BaseModel):
    datasets: list[dict[str, Any]]
    preview_hidden: bool


class PreprocessingStateResponse(BaseModel):
    summary_datasets: list[dict[str, Any]]
    dataset_options: list[dict[str, Any]]
    selected_periods: list[dict[str, Any]]
    filter_card: dict[str, Any] | None = None
    can_select_periods: bool
    can_filter: bool


class PeriodPreviewRequest(BaseModel):
    dataset_index: int
    selected_signals: list[int] | None = None


class PeriodPreviewResponse(BaseModel):
    dataset_index: int
    options: list[dict[str, Any]]
    selected_signals: list[int]
    figure: dict[str, Any]


class SavePeriodRequest(BaseModel):
    dataset_index: int
    relayout_data: dict[str, Any] | None = None
    selected_signals: list[int] = Field(default_factory=list)
    custom_name: str | None = None


class PeriodsMutationResponse(BaseModel):
    selected_periods: list[dict[str, Any]]
    filter_card: dict[str, Any] | None = None
    can_filter: bool | None = None
    period_preview: dict[str, Any] | None = None


class FilterApplyRequest(BaseModel):
    filter_type: int
    cutoff_low: float | None = None
    cutoff_high: float | None = None
    order: int


class FilterApplyResponse(BaseModel):
    period_options: list[dict[str, Any]]
    confirm_enabled: bool


class FilterFigureResponse(BaseModel):
    figure: dict[str, Any]


class AnalyzeStateResponse(BaseModel):
    summary_cards: list[dict[str, Any]]
    period_options: list[dict[str, Any]]
    selected_period: int | None
    can_calculate: bool
    has_results: bool


class AnalyzeAlertResponse(BaseModel):
    is_open: bool
    message: str | None
    color: str | None


class AnalyzeFigureResponse(BaseModel):
    role: str
    figure: dict[str, Any]
    playback: dict[str, Any] | None = None
    height_px: int | None = None


class AnalyzeCardResponse(BaseModel):
    title: str
    tables: list[list[dict[str, Any]]]
    figures: list[AnalyzeFigureResponse]


class AnalyzeSectionResponse(BaseModel):
    title: str
    items: list[AnalyzeCardResponse]
    empty_message: str | None = None


class AnalyzeResultsResponse(BaseModel):
    period_index: int
    overview: AnalyzeCardResponse
    sections: list[AnalyzeSectionResponse]


class AnalyzeCalculationRequest(BaseModel):
    selected_period: int | None = None


class AnalyzeCalculationResponse(BaseModel):
    alert: AnalyzeAlertResponse
    results: AnalyzeResultsResponse | None = None


class AnalyzeFramePreviewRequest(BaseModel):
    period_index: int
    label: str
    frame_count: int


class AnalyzeFramePreviewResponse(BaseModel):
    figure: dict[str, Any]
    frame_count: int
    max_frame_count: int


@router.get('/health')
def healthcheck() -> dict[str, str]:
    return {'status': 'ok'}


@router.post('/sessions', response_model=SessionResponse)
def create_session(payload: CreateSessionRequest) -> SessionResponse:
    record = session_store.create(label=payload.label)
    return _session_response(record)


@router.get('/sessions/{session_id}', response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    return _session_response(_get_session_record(session_id))


@router.get('/sessions/{session_id}/load/state', response_model=LoadStateResponse)
def get_load_state(session_id: str) -> LoadStateResponse:
    record = _get_session_record(session_id)
    browser = build_browser_payload(record.current_cwd, record.pending_load.vendor_type if record.pending_load else 2)
    return LoadStateResponse(cwd=browser['cwd'], datasets=serialize_loaded_datasets(record.loaded_datasets))


@router.post('/sessions/{session_id}/load/open', response_model=BrowserResponse)
def open_load_browser(session_id: str, payload: OpenBrowserRequest) -> BrowserResponse:
    record = _get_session_record(session_id)
    record.current_cwd = str(REPO_ROOT)
    browser = build_browser_payload(record.current_cwd, payload.vendor_type)
    record.current_cwd = browser['cwd']
    return BrowserResponse(**browser)


@router.post('/sessions/{session_id}/load/select-path', response_model=SelectPathResponse)
def select_load_path(session_id: str, payload: SelectPathRequest) -> SelectPathResponse:
    record = _get_session_record(session_id)
    selected_path = Path(payload.path)

    if selected_path.is_dir():
        browser = build_browser_payload(str(selected_path), payload.vendor_type)
        record.current_cwd = browser['cwd']
        return SelectPathResponse(mode='directory', browser=BrowserResponse(**browser))

    extension = selected_path.suffix.lower() if not selected_path.name.startswith('.') else selected_path.name.lower()
    allowed_extension = allowed_extension_for_type(payload.vendor_type)
    browser = build_browser_payload(str(selected_path.parent), payload.vendor_type)
    record.current_cwd = browser['cwd']

    if extension != allowed_extension:
        return SelectPathResponse(
            mode='invalid_file',
            browser=BrowserResponse(**browser),
            alert_open=True,
            alert_message='The selected file cannot be loaded',
        )

    try:
        pending = load_preview(str(selected_path), payload.vendor_type)
    except Exception as exc:  # pragma: no cover - defensive API guard
        return SelectPathResponse(
            mode='invalid_file',
            browser=BrowserResponse(**browser),
            alert_open=True,
            alert_message=f'The selected file cannot be loaded: {exc}',
        )

    record.pending_load = pending
    preview = build_preview_payload(pending)
    return SelectPathResponse(
        mode='file_loaded',
        browser=BrowserResponse(**browser),
        preview=PreviewResponse(**preview),
    )


@router.post('/sessions/{session_id}/load/preview', response_model=PreviewResponse)
def update_load_preview(session_id: str, payload: PreviewUpdateRequest) -> PreviewResponse:
    record = _get_session_record(session_id)
    if record.pending_load is None:
        raise HTTPException(status_code=400, detail='No pending file preview is available.')

    return PreviewResponse(**build_preview_payload(record.pending_load, payload.selected_signals))


@router.post('/sessions/{session_id}/load/cancel', response_model=LoadStateMutationResponse)
def cancel_load_preview(session_id: str) -> LoadStateMutationResponse:
    record = _get_session_record(session_id)
    record.pending_load = None
    return LoadStateMutationResponse(datasets=serialize_loaded_datasets(record.loaded_datasets), preview_hidden=True)


@router.post('/sessions/{session_id}/load/confirm', response_model=LoadStateMutationResponse)
def confirm_load_preview(session_id: str, payload: ConfirmDatasetRequest) -> LoadStateMutationResponse:
    record = _get_session_record(session_id)
    if record.pending_load is None:
        raise HTTPException(status_code=400, detail='No pending file preview is available.')

    dataset = confirm_loaded_dataset(
        record.pending_load,
        payload.relayout_data,
        payload.selected_signals,
        payload.custom_name,
    )
    record.loaded_datasets.append(dataset)
    record.reset_analyze_state()
    record.pending_load = None
    return LoadStateMutationResponse(datasets=serialize_loaded_datasets(record.loaded_datasets), preview_hidden=True)


@router.delete('/sessions/{session_id}/load/datasets/{dataset_label}', response_model=LoadStateMutationResponse)
def remove_loaded_dataset(session_id: str, dataset_label: str) -> LoadStateMutationResponse:
    record = _get_session_record(session_id)
    record.loaded_datasets = [dataset for dataset in record.loaded_datasets if dataset.label != dataset_label]
    record.reset_analyze_state()
    return LoadStateMutationResponse(datasets=serialize_loaded_datasets(record.loaded_datasets), preview_hidden=record.pending_load is None)


@router.get('/sessions/{session_id}/preprocessing/state', response_model=PreprocessingStateResponse)
def get_preprocessing_state(session_id: str) -> PreprocessingStateResponse:
    record = _get_session_record(session_id)
    return PreprocessingStateResponse(**build_preprocessing_state(record))


@router.post('/sessions/{session_id}/preprocessing/periods/preview', response_model=PeriodPreviewResponse)
def get_period_preview(session_id: str, payload: PeriodPreviewRequest) -> PeriodPreviewResponse:
    record = _get_session_record(session_id)
    return PeriodPreviewResponse(**build_period_preview(record, payload.dataset_index, payload.selected_signals))


@router.post('/sessions/{session_id}/preprocessing/periods', response_model=PeriodsMutationResponse)
def save_period_selection(session_id: str, payload: SavePeriodRequest) -> PeriodsMutationResponse:
    record = _get_session_record(session_id)
    return PeriodsMutationResponse(
        **add_stable_period(
            record,
            payload.dataset_index,
            payload.relayout_data,
            payload.selected_signals,
            payload.custom_name,
        ),
    )


@router.delete('/sessions/{session_id}/preprocessing/periods/{period_index}', response_model=PeriodsMutationResponse)
def delete_stable_period(session_id: str, period_index: int) -> PeriodsMutationResponse:
    record = _get_session_record(session_id)
    return PeriodsMutationResponse(**remove_stable_period(record, period_index))


@router.post('/sessions/{session_id}/preprocessing/filter/apply', response_model=FilterApplyResponse)
def apply_filter_to_periods(session_id: str, payload: FilterApplyRequest) -> FilterApplyResponse:
    record = _get_session_record(session_id)
    return FilterApplyResponse(
        **apply_filter_preview(record, payload.filter_type, payload.cutoff_low, payload.cutoff_high, payload.order),
    )


@router.get('/sessions/{session_id}/preprocessing/filter/preview/{period_index}', response_model=FilterFigureResponse)
def get_filtered_period_preview(session_id: str, period_index: int) -> FilterFigureResponse:
    record = _get_session_record(session_id)
    return FilterFigureResponse(**build_filtered_period_preview(record, period_index))


@router.post('/sessions/{session_id}/preprocessing/filter/confirm', response_model=PeriodsMutationResponse)
def confirm_filtered_periods(session_id: str) -> PeriodsMutationResponse:
    record = _get_session_record(session_id)
    return PeriodsMutationResponse(**confirm_filter_preview(record))


@router.delete('/sessions/{session_id}/preprocessing/filter/preview', response_model=FilterApplyResponse)
def cancel_filtered_preview(session_id: str) -> FilterApplyResponse:
    record = _get_session_record(session_id)
    return FilterApplyResponse(**cancel_filter_preview(record))


@router.delete('/sessions/{session_id}/preprocessing/filter', response_model=PeriodsMutationResponse)
def delete_saved_filter(session_id: str) -> PeriodsMutationResponse:
    record = _get_session_record(session_id)
    return PeriodsMutationResponse(**remove_saved_filter(record))


@router.get('/sessions/{session_id}/analyze/state', response_model=AnalyzeStateResponse)
def get_analyze_state(session_id: str) -> AnalyzeStateResponse:
    record = _get_session_record(session_id)
    return AnalyzeStateResponse(**build_analyze_state(record))


@router.post('/sessions/{session_id}/analyze/calculate', response_model=AnalyzeCalculationResponse)
def run_analyze_calculation(session_id: str, payload: AnalyzeCalculationRequest) -> AnalyzeCalculationResponse:
    record = _get_session_record(session_id)
    return AnalyzeCalculationResponse(**calculate_results(record, payload.selected_period))


@router.get('/sessions/{session_id}/analyze/results', response_model=AnalyzeResultsResponse)
def get_analyze_results(session_id: str, period_index: int) -> AnalyzeResultsResponse:
    record = _get_session_record(session_id)
    results = build_analyze_results(record, period_index)
    if results is None:
        raise HTTPException(status_code=400, detail='No analysis results are available for the selected period.')
    return AnalyzeResultsResponse(**results)


@router.post('/sessions/{session_id}/analyze/eit-frame-preview', response_model=AnalyzeFramePreviewResponse)
def get_analyze_eit_frame_preview(
    session_id: str,
    payload: AnalyzeFramePreviewRequest,
) -> AnalyzeFramePreviewResponse:
    record = _get_session_record(session_id)
    return AnalyzeFramePreviewResponse(
        **build_eit_frame_preview(record, payload.period_index, payload.label, payload.frame_count),
    )


def _get_session_record(session_id: str) -> SessionRecord:
    try:
        return session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _session_response(record: SessionRecord) -> SessionResponse:
    return SessionResponse(
        session_id=record.session_id,
        label=record.label,
        created_at=record.created_at,
    )
