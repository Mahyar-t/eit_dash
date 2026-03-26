from __future__ import annotations

import re
from typing import TYPE_CHECKING

import dash_bootstrap_components as dbc
import numpy as np
import plotly.colors
import plotly.graph_objects as go
from dash import html

from eit_dash.definitions import element_ids as ids
from eit_dash.definitions import layout_styles as styles
from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.utils.time_axis import build_time_axis_context

if TYPE_CHECKING:
    from eitprocessing.datahandling.sequence import Sequence

    from eit_dash.utils.data_singleton import Period


def blank_fig():
    """Create an empty figure."""
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template='plotly_dark')
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)

    return apply_figure_theme(fig)


def apply_figure_theme(figure: go.Figure) -> go.Figure:
    """Apply the shared glass theme to Plotly figures."""
    figure.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(15, 23, 42, 0.9)',
        plot_bgcolor='rgba(11, 17, 32, 0.95)',
        font={'color': '#f8f9fa', 'family': 'Avenir Next, Segoe UI, Trebuchet MS, sans-serif'},
        title={'automargin': True, 'y': 0.97},
        legend={
            'bgcolor': 'rgba(15, 23, 42, 0.9)',
            'bordercolor': 'rgba(255, 255, 255, 0.2)',
            'borderwidth': 1,
            'font': {'color': '#f8f9fa'},
        },
        margin={'t': 56, 'l': 24, 'b': 56, 'r': 24},
        hoverlabel={'bgcolor': '#0f172a', 'font': {'color': '#f8f9fa'}},
    )
    figure.update_xaxes(
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=False,
        linecolor='rgba(255, 255, 255, 0.2)',
        tickcolor='rgba(255, 255, 255, 0.3)',
        color='#f8f9fa',
        rangeslider={
            'bgcolor': 'rgba(15, 23, 42, 0.6)',
            'bordercolor': 'rgba(255, 255, 255, 0.2)',
            'thickness': 0.1,
        },
        automargin=True,
        title_standoff=18,
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=False,
        linecolor='rgba(255, 255, 255, 0.2)',
        tickcolor='rgba(255, 255, 255, 0.3)',
        color='#f8f9fa',
        automargin=True,
        title_standoff=16,
    )

    return figure


def create_filter_results_card(parameters: dict) -> dbc.Card:
    """
    Create the card with the information on the parameters used for filtering the data.

    Args:
        parameters: dictionary containing the filter information
    """
    rows = [
        ('Filter type', parameters.get('filter_type', '')),
        ('Cutoff frequency', parameters.get('cutoff_frequency', '')),
        ('Order', parameters.get('order', '')),
        ('Sample frequency', parameters.get('sample_frequency', '')),
    ]

    table = html.Table(
        [html.Tbody([
            html.Tr([
                html.Td(label, className='info-table__label'),
                html.Td(str(value), className='info-table__value'),
            ])
            for label, value in rows
        ])],
        className='info-table',
    )

    card_list = [
        html.H4('Data filtered', className='card-title'),
        table,
        dbc.Button(
            'Remove',
            id=ids.REMOVE_FILTER_BUTTON,
            className='glass-card__action mt-3',
        ),
    ]

    return dbc.Card(dbc.CardBody(card_list), id=ids.FILTERING_SAVED_CARD, className='glass-card')


def create_info_card(dataset: Sequence, remove_button: bool = False) -> dbc.Card:
    """Create the card with the information on the loaded dataset to be displayed in the Results section.

    Args:
        dataset: Sequence object containing the selected dataset
        remove_button: add the remove button if set to True
    """
    vendor_val = getattr(dataset.eit_data['raw'].vendor, 'value', str(dataset.eit_data['raw'].vendor))

    rows = [
        ('Name', dataset.label),
        ('Frames', dataset.eit_data['raw'].nframes),
        ('Start time', f"{dataset.eit_data['raw'].time[0]:.3f} ms"),
        ('End time', f"{dataset.eit_data['raw'].time[-1]:.3f} ms"),
        ('Vendor', vendor_val),
        ('Signals', ', '.join(list(dataset.continuous_data))),
        ('Path', str(dataset.eit_data['raw'].path)),
    ]

    table = html.Table(
        [html.Tbody([
            html.Tr([
                html.Td(label, className='info-table__label'),
                html.Td(str(value), className='info-table__value'),
            ])
            for label, value in rows
        ])],
        className='info-table',
    )

    card_list = [
        html.H4(dataset.label, className='card-title'),
        table,
    ]
    if remove_button:
        card_list += [
            dbc.Button(
                'Remove',
                id={'type': ids.REMOVE_DATA_BUTTON, 'index': dataset.label},
                className='glass-card__action mt-3',
            ),
        ]
    return dbc.Card(dbc.CardBody(card_list), id=dataset.label, className='glass-card')



def create_selected_period_card(
    period: Sequence,
    dataset: str,
    index: int,
    remove_button: bool = True,
) -> dbc.Card:
    """
    Create the card with the information on the selected period to be displayed in the Results section.

    Args:
        period: Sequence object containing the selected period
        dataset: The original dataset from which the period has been selected
        index: of the period
        remove_button: add the remove button if set to True
    """
    rows = [
        ('Name', period.label),
        ('Frames', period.eit_data['raw'].nframes),
        ('Start time', f"{period.eit_data['raw'].time[0]:.3f} ms"),
        ('End time', f"{period.eit_data['raw'].time[-1]:.3f} ms"),
        ('Dataset', dataset),
    ]

    table = html.Table(
        [html.Tbody([
            html.Tr([
                html.Td(label, className='info-table__label'),
                html.Td(str(value), className='info-table__value'),
            ])
            for label, value in rows
        ])],
        className='info-table',
    )

    card_list = [
        html.H4(period.label, className='card-title'),
        table,
    ]
    if remove_button:
        card_list += [
            dbc.Button(
                'Remove',
                id={'type': ids.REMOVE_PERIOD_BUTTON, 'index': str(index)},
                className='glass-card__action mt-3',
            ),
        ]

    return dbc.Card(
        dbc.CardBody(card_list),
        id={'type': ids.PERIOD_CARD, 'index': str(index)},
        className='glass-card',
    )


def create_slider_figure(
    dataset: Sequence,
    continuous_data: list[str] | None = None,
    clickable_legend: bool = False,
) -> go.Figure:
    """Create the figure for the selection of range. The raw global impedance is plotted by default.

    Args:
        dataset: Sequence object containing the selected dataset
        continuous_data: list of the continuous data signals to be plotted
        clickable_legend: if True, the user can hide a signal by clicking on the legend
    """
    figure = go.Figure()
    params = {}
    y_position = 0
    colors = plotly.colors.DEFAULT_PLOTLY_COLORS

    if continuous_data is None:
        continuous_data = []

    if RAW_EIT_LABEL not in dataset.continuous_data:
        keys = list(dataset.continuous_data.keys()) if hasattr(dataset.continuous_data, "keys") else list(dataset.continuous_data)
        raise KeyError(f"Expected '{RAW_EIT_LABEL}' not found. Available keys: {keys}")

    dataset_start_time = float(dataset.continuous_data[RAW_EIT_LABEL].time[0])
    raw_time_context = build_time_axis_context(
        dataset.continuous_data[RAW_EIT_LABEL].time,
        dataset_start_time=dataset_start_time,
    )

    figure.add_trace(
        go.Scatter(
            x=raw_time_context.x,
            y=dataset.continuous_data[RAW_EIT_LABEL].values,
            customdata=raw_time_context.customdata,
            hovertemplate=raw_time_context.hovertemplate,
            name=RAW_EIT_LABEL,
            line={'color': colors[0]},
        ),
    )
    figure.update_yaxes(
        color=colors[0],
        title=f"{RAW_EIT_LABEL} {dataset.continuous_data[RAW_EIT_LABEL].unit}",
    )

    for n, cont_signal in enumerate(continuous_data):
        if cont_signal != RAW_EIT_LABEL:
            color = colors[(n + 1) % len(colors)]
            time_context = build_time_axis_context(
                dataset.continuous_data[cont_signal].time,
                dataset_start_time=dataset_start_time,
            )
            figure.add_trace(
                go.Scatter(
                    x=time_context.x,
                    y=dataset.continuous_data[cont_signal].values,
                    customdata=time_context.customdata,
                    hovertemplate=time_context.hovertemplate,
                    name=cont_signal,
                    line={'color': color},
                    opacity=0.5,
                    yaxis=f'y{n + 2}',
                ),
            )
            side = 'right' if n % 2 == 0 else 'left'

            y_position += 0.1
            new_y = {
                'title': f"{cont_signal} {dataset.continuous_data[cont_signal].unit}",
                'anchor': 'free',
                'overlaying': 'y',
                'side': side,
                'autoshift': True,
                'color': color,
            }

            param_name = f'yaxis{n + 2}'
            params.update({param_name: new_y})

    if hasattr(dataset, 'sparse_data'):
        for key in dataset.sparse_data:
            if re.match('events', key):
                for k, v in enumerate(dataset.sparse_data[key].values):
                    annotation = {'text': f'{v.text}', 'textangle': -90}
                    figure.add_vline(
                        x=dataset.sparse_data[key].time[k],
                        line_width=3,
                        line_dash='dash',
                        line_color='green',
                        annotation=annotation,
                    )
                break

    figure.update_layout(
        xaxis={'rangeslider': {'visible': True}, 'title': raw_time_context.axis_title},
        margin={'t': 0, 'l': 0, 'b': 0, 'r': 0},
        **params,
    )

    if not clickable_legend:
        figure.update_layout(legend={'itemclick': False, 'itemdoubleclick': False})

    return apply_figure_theme(figure)


def mark_selected_periods(
    original_figure: go.Figure | dict,
    periods: list[Period],
    dataset_start_times: dict[int, float],
) -> go.Figure:
    """
    Create the figure for the selection of range.

    Args:
        original_figure: figure to update
        periods: list of Sequence object containing the selected dataset.
        These ranges, the signal is plotted in black
    """
    for period in periods:
        seq = period.get_data()
        period_index = period.get_period_index()
        if period_index not in dataset_start_times:
            msg = f"Missing dataset start time for period {period_index}"
            raise KeyError(msg)

        for n, cont_signal in enumerate(seq.continuous_data):
            time_context = build_time_axis_context(
                seq.continuous_data[cont_signal].time,
                dataset_start_time=dataset_start_times[period_index],
                selection_start_time=float(seq.continuous_data[cont_signal].time[0]),
            )
            params = {
                'x': time_context.x,
                'y': seq.continuous_data[cont_signal].values,
                'customdata': time_context.customdata,
                'hovertemplate': time_context.hovertemplate,
                'name': cont_signal,
                'meta': {'uid': period_index},
                'line': {'color': '#22c55e'},
                'showlegend': False,
            }
            if cont_signal != RAW_EIT_LABEL:
                params.update(
                    {
                        'opacity': 0.5,
                        'yaxis': f'y{n + 2}',
                    },
                )
            selected_signal = go.Scatter(**params).to_plotly_json()

            if isinstance(original_figure, go.Figure):
                original_figure.add_trace(selected_signal)
            else:
                original_figure['data'].append(selected_signal)

    return original_figure


def update_figure_signal_visibility(
    figure: go.Figure | dict,
    visible_signal_names: list[str] | set[str],
) -> go.Figure | dict:
    """Keep trace and y-axis visibility aligned with the selected signals."""
    visible_names = set(visible_signal_names)
    axis_visibility: dict[str, bool] = {}

    for trace in figure["data"]:
        axis_ref = trace.get("yaxis") or "y"
        axis_name = axis_ref.replace("y", "yaxis", 1)
        is_visible = trace["name"] in visible_names

        trace["visible"] = is_visible
        axis_visibility[axis_name] = axis_visibility.get(axis_name, False) or is_visible

    for axis_name, is_visible in axis_visibility.items():
        if axis_name in figure["layout"]:
            figure["layout"][axis_name]["visible"] = is_visible

    return figure


def get_signal_options(
    dataset: Sequence,
    show_eit: bool = False,
) -> list[dict[str, int | str]]:
    """Get the options for signal selection to be shown in the signal selection section.

    Args:
        dataset: Sequence object containing the selected dataset
        show_eit: include eit data in the option if True. Default false
    Returns:
        A list of label - value options for populating the options list
    """
    options = []

    if dataset.continuous_data:
        for cont in dataset.continuous_data:
            values = np.asarray(dataset.continuous_data[cont].values)
            has_finite_values = np.isfinite(values).any()
            if ((cont == RAW_EIT_LABEL and show_eit) or (cont != RAW_EIT_LABEL and has_finite_values)):
                options.append({'label': cont, 'value': len(options)})

    return options


def get_selections_slidebar(slidebar_stat: dict) -> tuple:
    """Given the layout data of a graph slidebar, it returns the first and the last sample selected.

    Args:
        slidebar_stat: Layout data of a graph slidebar.

    Returns:
        A tuple where the first value is the starting sample and the second value is the
        end sample. If a sample cannot be determined, None is returned.
    """
    if 'xaxis.range' in slidebar_stat:
        start_sample = slidebar_stat['xaxis.range'][0]
        stop_sample = slidebar_stat['xaxis.range'][1]
    elif ('xaxis.range[0]' in slidebar_stat) and ('xaxis.range[1]' in slidebar_stat):
        start_sample = slidebar_stat['xaxis.range[0]']
        stop_sample = slidebar_stat['xaxis.range[1]']
    else:
        start_sample = stop_sample = None

    return start_sample, stop_sample
