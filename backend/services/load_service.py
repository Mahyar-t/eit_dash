from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from eitprocessing.datahandling.loading import load_eit_data

from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.definitions.option_lists import InputFiletypes
from eit_dash.utils.common import (
    create_slider_figure,
    get_selections_slidebar,
    get_signal_options,
    update_figure_signal_visibility,
)

if TYPE_CHECKING:
    from eitprocessing.datahandling.sequence import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class PendingLoadState:
    source_path: str
    vendor_type: int
    sequence: Sequence
    options: list[dict[str, int | str]] = field(default_factory=list)
    base_figure: dict[str, Any] = field(default_factory=dict)


def vendor_name_from_type(vendor_type: int) -> str:
    return InputFiletypes(int(vendor_type)).name.lower()


def allowed_extension_for_type(vendor_type: int) -> str:
    vendor_id = int(vendor_type)
    if vendor_id == InputFiletypes.Draeger.value:
        return '.bin'
    if vendor_id == InputFiletypes.Timpel.value:
        return '.txt'
    if vendor_id == InputFiletypes.Sentec.value:
        return '.zri'

    msg = f'Unsupported vendor type: {vendor_type}'
    raise ValueError(msg)


def list_browser_entries(cwd: str, vendor_type: int) -> list[dict[str, Any]]:
    path = Path(cwd)
    allowed_ext = allowed_extension_for_type(vendor_type)
    entries: list[dict[str, Any]] = []

    if not path.is_dir():
        return entries

    for item in sorted(path.iterdir(), key=lambda child: child.name.lower()):
        extension = item.suffix.lower() if not item.name.startswith('.') else item.name.lower()
        is_dir = item.is_dir()
        if is_dir or extension == allowed_ext:
            entries.append(
                {
                    'name': item.name,
                    'path': str(item),
                    'is_dir': is_dir,
                    'icon': '📂' if is_dir else allowed_ext.replace('.', '').upper(),
                    'icon_class': 'browser-icon folder-icon' if is_dir else 'browser-icon file-icon-text',
                }
            )

    return entries


def build_browser_payload(cwd: str, vendor_type: int) -> dict[str, Any]:
    path = Path(cwd)
    effective_cwd = path if path.is_dir() else path.parent
    return {
        'cwd': str(effective_cwd),
        'entries': list_browser_entries(str(effective_cwd), vendor_type),
    }


def load_preview(path: str, vendor_type: int) -> PendingLoadState:
    data_path = Path(path)
    sequence = load_eit_data(data_path, vendor=vendor_name_from_type(vendor_type), label='selected data')
    options = get_signal_options(sequence)
    preview_signals = [RAW_EIT_LABEL, *[str(option['label']) for option in options]]
    base_figure = create_slider_figure(sequence, continuous_data=preview_signals, clickable_legend=True).to_dict()
    return PendingLoadState(
        source_path=str(data_path),
        vendor_type=vendor_type,
        sequence=sequence,
        options=options,
        base_figure=base_figure,
    )


def build_preview_payload(pending: PendingLoadState, selected_signals: list[int] | None = None) -> dict[str, Any]:
    selected = pending.options if selected_signals is None else [
        option for option in pending.options if int(option['value']) in {int(value) for value in selected_signals}
    ]
    visible_signal_names = [RAW_EIT_LABEL, *[str(option['label']) for option in selected]]
    figure = update_figure_signal_visibility(deepcopy(pending.base_figure), visible_signal_names)
    return {
        'source_path': pending.source_path,
        'options': pending.options,
        'selected_signals': [int(option['value']) for option in selected],
        'figure': figure,
    }


def serialize_dataset(dataset: Sequence) -> dict[str, Any]:
    vendor_val = getattr(dataset.eit_data['raw'].vendor, 'value', str(dataset.eit_data['raw'].vendor))
    return {
        'label': dataset.label,
        'title': dataset.label,
        'rows': [
            {'label': 'Name', 'value': dataset.label},
            {'label': 'Frames', 'value': dataset.eit_data['raw'].nframes},
            {'label': 'Start time', 'value': f"{dataset.eit_data['raw'].time[0]:.3f} s"},
            {'label': 'End time', 'value': f"{dataset.eit_data['raw'].time[-1]:.3f} s"},
            {'label': 'Vendor', 'value': vendor_val},
            {'label': 'Signals', 'value': ', '.join(list(dataset.continuous_data))},
            {'label': 'Path', 'value': str(dataset.eit_data['raw'].path)},
        ],
    }


def serialize_loaded_datasets(datasets: list[Sequence]) -> list[dict[str, Any]]:
    return [serialize_dataset(dataset) for dataset in datasets]


def confirm_loaded_dataset(
    pending: PendingLoadState,
    relayout_data: dict[str, Any] | None,
    selected_signals: list[int] | None,
    custom_name: str | None,
) -> Sequence:
    raw_signal = pending.sequence.continuous_data[RAW_EIT_LABEL]
    if relayout_data is not None:
        start_sample, stop_sample = get_selections_slidebar(relayout_data)
        if not start_sample:
            start_sample = raw_signal.time[0]
        if not stop_sample:
            stop_sample = raw_signal.time[-1]
    else:
        start_sample = raw_signal.time[0]
        stop_sample = raw_signal.time[-1]

    dataset_name = custom_name.strip() if custom_name and custom_name.strip() else Path(pending.source_path).name
    selected_values = {int(value) for value in (selected_signals or [])}
    selected_labels = {str(option['label']) for option in pending.options if int(option['value']) in selected_values}

    cut_data = pending.sequence.select_by_time(start_sample, stop_sample)
    for data_type in list(cut_data.continuous_data.keys()):
        if data_type != RAW_EIT_LABEL and data_type not in selected_labels:
            cut_data.continuous_data.pop(data_type)

    cut_data.label = dataset_name
    return cut_data
