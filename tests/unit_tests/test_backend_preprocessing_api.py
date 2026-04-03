from fastapi.testclient import TestClient

from backend.app import app
from tests.conftest import data_path

client = TestClient(app)


def test_period_preview_defaults_to_all_available_signals():
    session_response = client.post('/api/sessions', json={'label': 'Preprocessing API test'})
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

    period_preview_response = client.post(
        f'/api/sessions/{session_id}/preprocessing/periods/preview',
        json={'dataset_index': 0},
    )
    assert period_preview_response.status_code == 200

    payload = period_preview_response.json()
    option_values = [option['value'] for option in payload['options']]
    option_labels = [option['label'] for option in payload['options']]

    assert payload['selected_signals'] == option_values
    assert 'global_impedance_(raw)' in option_labels

