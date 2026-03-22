from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx, html
from dash.exceptions import PreventUpdate
from eitprocessing.datahandling.loading import load_eit_data

import eit_dash.definitions.element_ids as ids
from eit_dash.app import data_object
from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.definitions.option_lists import InputFiletypes
from eit_dash.utils.common import (
    create_info_card,
    create_slider_figure,
    get_selections_slidebar,
    get_signal_options,
)

if TYPE_CHECKING:
    from eitprocessing.datahandling.sequence import Sequence

file_data: Sequence | None = None


# managing the file selection. Confirm button clicked
@callback(
    Output(ids.CHOOSE_DATA_POPUP, "is_open"),
    Output(ids.NFILES_PLACEHOLDER, "children"),
    Output(ids.ALERT_LOAD, "is_open"),
    Input(ids.SELECT_FILES_BUTTON, "n_clicks"),
    Input(ids.STORED_CWD, "data"),
    State(ids.INPUT_TYPE_SELECTOR, "value"),
    prevent_initial_call=True,
)
def select_file(
    select_file,
    file_path,
    file_type,
):
    """Check if the selected file is compatible and closes the popup."""
    open_modal = True
    data = None
    show_alert = False
    read_data_flag = False

    trigger = ctx.triggered_id

    # when the button for selecting the file has been clicked
    if trigger == ids.SELECT_FILES_BUTTON:
        data = None  # Reset selection state, do not pass CWD to loader.

    if trigger == ids.STORED_CWD and file_path:
        path = Path(file_path)
        
        if path.is_file():
            extension = path.suffix.lower() if not path.name.startswith(".") else path.name.lower()
            int_type = int(file_type)

            # check if the file extension is compatible with the file type selected
            if (
                (int_type == InputFiletypes.Draeger.value and extension == ".bin")
                or (int_type == InputFiletypes.Timpel.value and extension == ".txt")
                or (int_type == InputFiletypes.Sentec.value and extension == ".zri")
            ):
                read_data_flag = True

            # if the type check is ok, then close the file selector and read the data
            if read_data_flag:
                data = file_path
                open_modal = False

            # if it's not ok, then show an alert
            else:
                show_alert = True
        else:
            # If it's a directory, do nothing (modal stays open, directory navigation happens elsewhere)
            raise PreventUpdate

    return open_modal, data, show_alert


@callback(
    Output(ids.DATA_SELECTOR_OPTIONS, "hidden", allow_duplicate=True),
    Output(ids.CHECKBOX_SIGNALS, "options"),
    Output(ids.CHECKBOX_SIGNALS, "value"),
    Output(ids.FILE_LENGTH_SLIDER, "figure"),
    Input(ids.NFILES_PLACEHOLDER, "children"),
    Input(ids.LOAD_CANCEL_BUTTON, "n_clicks"),
    Input(ids.CHECKBOX_SIGNALS, "value"),
    State(ids.INPUT_TYPE_SELECTOR, "value"),
    State(ids.FILE_LENGTH_SLIDER, "figure"),
    prevent_initial_call=True,
)
def load_selected_data(data_path, cancel_load, sig, file_type, fig):
    """Read the file selected in the file selector."""
    global file_data

    trigger = ctx.triggered_id

    # cancelled selection. Reset the data and turn off the data selector
    if trigger == ids.LOAD_CANCEL_BUTTON:
        data_path = None
        file_data = None
        options = ticked = []

    if not data_path:
        # this is needed, because a figure object must be returned for the graph, even if empty
        figure = go.Figure()
        return True, [], [], figure

    if trigger in [ids.NFILES_PLACEHOLDER, ids.CHECKBOX_SIGNALS]:
        if trigger == ids.CHECKBOX_SIGNALS:
            options = get_signal_options(file_data)
            figure = fig
            ticked = sig
        else:
            path = Path(data_path)
            print(f"[DEBUG] Loading: {path} | vendor: {InputFiletypes(int(file_type)).name.lower()} | is_file: {path.is_file()}")
            file_data = load_eit_data(
                path,
                vendor=InputFiletypes(int(file_type)).name.lower(),
                label="selected data",
            )
            print(f"[DEBUG] Loaded. continuous_data keys: {list(file_data.continuous_data.keys())}")

            options = get_signal_options(file_data)

            figure = create_slider_figure(
                file_data,
                continuous_data=list(file_data.continuous_data),
                clickable_legend=True,
            )
            ticked = [s["value"] for s in options]

        ok = [RAW_EIT_LABEL]
        if ticked:
            ok += [options[s]["label"] for s in ticked]

        for s in figure["data"]:
            is_visible = (s["name"] in ok)
            s["visible"] = True if is_visible else False
            
            if "yaxis" in s and s["yaxis"]:
                # Map 'y2' -> 'yaxis2' 
                axis_name = s["yaxis"].replace("y", "yaxis")
                if axis_name in figure["layout"]:
                    figure["layout"][axis_name]["visible"] = is_visible

    return False, options, ticked, figure


@callback(
    Output(ids.DATASET_CONTAINER, "children", allow_duplicate=True),
    Output(ids.DATA_SELECTOR_OPTIONS, "hidden", allow_duplicate=True),
    Input(ids.LOAD_CONFIRM_BUTTON, "n_clicks"),
    State(ids.NFILES_PLACEHOLDER, "children"),
    State(ids.DATASET_CONTAINER, "children"),
    State(ids.INPUT_TYPE_SELECTOR, "value"),
    State(ids.FILE_LENGTH_SLIDER, "relayoutData"),
    State(ids.CHECKBOX_SIGNALS, "value"),
    State(ids.CHECKBOX_SIGNALS, "options"),
    prevent_initial_call=True,
)
def show_info(
    btn_click,
    loaded_data,
    container_state,
    filetype,
    slidebar_stat,
    selected_signals,
    signals_options,
):
    """Creates the preview for preselecting part of the dataset."""
    if file_data:
        # get the first and last sample selected in the slidebar
        if slidebar_stat is not None:
            start_sample, stop_sample = get_selections_slidebar(slidebar_stat)

            if not start_sample:
                start_sample = file_data.continuous_data[RAW_EIT_LABEL].time[0]
            if not stop_sample:
                stop_sample = file_data.continuous_data[RAW_EIT_LABEL].time[-1]
        else:
            start_sample = file_data.continuous_data[RAW_EIT_LABEL].time[0]
            stop_sample = file_data.continuous_data[RAW_EIT_LABEL].time[-1]

        dataset_name = data_object.get_next_dataset_label()

        selected_signals = selected_signals or []
        # get the name of the selected continuous signals
        selected = [signals_options[s]["label"] for s in selected_signals]

        # cut the data
        cut_data = file_data.select_by_time(start_sample, stop_sample)

        for data_type in file_data.continuous_data:
            # add just the selected signals and the raw EIT
            if not (data_type in selected or data_type == RAW_EIT_LABEL):
                cut_data.continuous_data.pop(data_type)

        # reassign the label
        cut_data.label = dataset_name

        # save the selected data in the singleton
        data_object.add_sequence(cut_data)

        # create the info summary card
        card = create_info_card(cut_data, remove_button=True)

        # add the card to the current results
        if container_state:
            container_state += [card]
        else:
            container_state = [card]

        # hide the pre-selection UI after confirming
        return container_state, True

    return container_state, True


# file browser
@callback(
    Output(ids.CWD, "children"),
    Input(ids.STORED_CWD, "data"),
    Input(ids.PARENT_DIR, "n_clicks"),
    Input(ids.CWD, "children"),
    prevent_initial_call=True,
)
def get_parent_directory(stored_cwd, n_clicks, currentdir):
    """Return path of parent directory."""
    triggered_id = ctx.triggered_id
    if triggered_id == ids.STORED_CWD:
        return stored_cwd
    return str(Path(currentdir).parent)


@callback(
    Output(ids.CWD_FILES, "children"),
    Input(ids.CWD, "children"),
    Input(ids.INPUT_TYPE_SELECTOR, "value"),
)
def list_cwd_files(cwd, vendor_type):
    """List files in the directory."""
    path = Path(cwd)

    allowed_ext = None
    if vendor_type:
        vendor_id = int(vendor_type)
        if vendor_id == InputFiletypes.Draeger.value:
            allowed_ext = ".bin"
        elif vendor_id == InputFiletypes.Timpel.value:
            allowed_ext = ".txt"
        elif vendor_id == InputFiletypes.Sentec.value:
            allowed_ext = ".zri"

    cwd_files = []
    if path.is_dir():
        files = sorted(os.listdir(path), key=str.lower)
        for i, file in enumerate(files):
            filepath = Path(file)
            full_path = Path(cwd) / filepath

            is_dir = Path(full_path).is_dir()
            extension = filepath.suffix if not filepath.name.startswith(".") else filepath.name

            if is_dir or (allowed_ext and extension == allowed_ext):
                icon = "📂" if is_dir else extension.replace(".", "").upper()
                icon_class = "browser-icon folder-icon" if is_dir else "browser-icon file-icon-text"
                item = html.A(
                    [
                        html.Div(icon, className=icon_class),
                        html.Div(file, className="browser-item-name"),
                    ],
                    id={"type": "listed_file", "index": i},
                    title=str(full_path),
                    href="#",
                    className="browser-grid-item",
                )
                cwd_files.append(item)
    return cwd_files


@callback(
    Output(ids.STORED_CWD, "data"),
    Input({"type": "listed_file", "index": ALL}, "n_clicks"),
    Input(ids.SELECT_FILES_BUTTON, "n_clicks"),
    State({"type": "listed_file", "index": ALL}, "title"),
    prevent_initial_call=True,
)
def store_clicked_file(n_clicks, select_btn, title):
    """Saves path of currently clicked file or resets to root."""
    trigger = ctx.triggered_id
    if not trigger:
        raise PreventUpdate

    if trigger == ids.SELECT_FILES_BUTTON:
        return str(Path.cwd())

    if not n_clicks or set(n_clicks) == {None}:
        raise PreventUpdate
    index = trigger["index"]
    for state in ctx.states_list[0]:
        if state["id"]["index"] == index:
            return state["value"]

    return None


@callback(
    Output(ids.DATASET_CONTAINER, "children", allow_duplicate=True),
    [
        Input({"type": ids.REMOVE_DATA_BUTTON, "index": ALL}, "n_clicks"),
    ],
    [
        State(ids.DATASET_CONTAINER, "children"),
    ],
    prevent_initial_call=True,
)
def remove_dataset(n_clicks, container):
    """React to clicking the remove button of a dataset.

    Removes the card from the results and the dataset from the loaded selections.
    """
    # at the element creation time, the update should be avoided
    if all(element is None for element in n_clicks):
        raise PreventUpdate

    input_id = ctx.triggered_id["index"]

    # remove from the singleton
    data_object.remove_data(input_id)

    return [card for card in container if f"'index': '{input_id}'" not in str(card)]


# Repopulate data after reload
@callback(
    Output(ids.DATASET_CONTAINER, "children", allow_duplicate=True),
    Input(ids.POPULATE_DATA, "children"),
    prevent_initial_call="initial_duplicate",
)
def repopulate_data(reload):
    """Repopulate data after reloading page."""
    # create the info summary card
    reloaded_data = data_object.get_all_sequences()
    return [create_info_card(element, remove_button=True) for element in reloaded_data]
