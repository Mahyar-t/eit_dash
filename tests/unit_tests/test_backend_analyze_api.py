from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient
from eitprocessing.datahandling.sparsedata import SparseData

from backend.app import app
from eit_dash.definitions.constants import FILTERED_EIT_LABEL
from tests.conftest import data_path

client = TestClient(app)

FIRST_SAMPLE = 100
LAST_SAMPLE = 600


def _prepare_session_with_period(file_data) -> str:
    session_response = client.post('/api/sessions', json={'label': 'Analyze API test'})
    assert session_response.status_code == 200
    session_id = session_response.json()['session_id']

    open_response = client.post(f'/api/sessions/{session_id}/load/open', json={'vendor_type': 1})
    assert open_response.status_code == 200

    preview_response = client.post(
        f'/api/sessions/{session_id}/load/select-path',
        json={'path': str(data_path), 'vendor_type': 1},
    )
    assert preview_response.status_code == 200
    assert preview_response.json()['mode'] == 'file_loaded'

    confirm_response = client.post(
        f'/api/sessions/{session_id}/load/confirm',
        json={
            'relayout_data': None,
            'selected_signals': [],
            'custom_name': None,
        },
    )
    assert confirm_response.status_code == 200

    save_period_response = client.post(
        f'/api/sessions/{session_id}/preprocessing/periods',
        json={
            'dataset_index': 0,
            'relayout_data': {
                'xaxis.range': [file_data.time[FIRST_SAMPLE], file_data.time[LAST_SAMPLE]],
            },
            'selected_signals': [],
            'custom_name': 'Period 0',
        },
    )
    assert save_period_response.status_code == 200
    return session_id


def test_analyze_api_roundtrip(file_data):
    session_id = _prepare_session_with_period(file_data)

    state_response = client.get(f'/api/sessions/{session_id}/analyze/state')
    assert state_response.status_code == 200
    state_payload = state_response.json()
    assert state_payload['can_calculate'] is True
    assert len(state_payload['summary_cards']) >= 2
    assert state_payload['period_options'] == [{'label': 'Period 0', 'value': 0}]

    calculate_response = client.post(
        f'/api/sessions/{session_id}/analyze/calculate',
        json={'selected_period': 0},
    )
    assert calculate_response.status_code == 200
    calculation_payload = calculate_response.json()
    assert calculation_payload['alert']['color'] == 'success'
    assert calculation_payload['results']['overview']['title'] == 'Output Overview'

    results_response = client.get(f'/api/sessions/{session_id}/analyze/results', params={'period_index': 0})
    assert results_response.status_code == 200
    results_payload = results_response.json()
    section_titles = [section['title'] for section in results_payload['sections']]
    assert section_titles[0] == 'EIT Data (1)'
    assert section_titles[1] == 'Continuous Data (1)'
    assert section_titles[2].startswith('Sparse Data (')
    assert section_titles[3] == 'Interval Data (0)'
    sparse_items = results_payload['sections'][2]['items']
    assert 'continuous_eelis' in [item['title'] for item in sparse_items]

    frame_response = client.post(
        f'/api/sessions/{session_id}/analyze/eit-frame-preview',
        json={'period_index': 0, 'label': 'raw', 'frame_count': 3},
    )
    assert frame_response.status_code == 200
    frame_payload = frame_response.json()
    assert frame_payload['frame_count'] == 3
    assert len(frame_payload['figure']['frames']) == 3


def test_analyze_api_prefers_filtered_signal_when_available(file_data):
    session_id = _prepare_session_with_period(file_data)

    filter_apply_response = client.post(
        f'/api/sessions/{session_id}/preprocessing/filter/apply',
        json={
            'filter_type': 0,
            'cutoff_low': 0.5,
            'cutoff_high': None,
            'order': 2,
        },
    )
    assert filter_apply_response.status_code == 200
    assert filter_apply_response.json()['confirm_enabled'] is True

    confirm_filter_response = client.post(f'/api/sessions/{session_id}/preprocessing/filter/confirm')
    assert confirm_filter_response.status_code == 200

    class StubEELI:
        seen_label = None

        def compute_parameter(self, signal):
            StubEELI.seen_label = signal.label
            return SparseData(
                label='continuous_eelis',
                name='End-expiratory lung impedance (EELI)',
                unit=None,
                category='impedance',
                time=np.array([signal.time[0]]),
                values=np.array([0.1]),
            )

    with patch('backend.services.analyze_service.EELI', new=StubEELI):
        calculate_response = client.post(
            f'/api/sessions/{session_id}/analyze/calculate',
            json={'selected_period': 0},
        )

    assert calculate_response.status_code == 200
    assert calculate_response.json()['alert']['color'] == 'success'
    assert StubEELI.seen_label == FILTERED_EIT_LABEL
