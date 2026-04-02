from fastapi.testclient import TestClient

from backend.app import app
from eit_dash.definitions.constants import RAW_EIT_LABEL
from tests.conftest import data_path

client = TestClient(app)

FIRST_SAMPLE = 100
LAST_SAMPLE = 1000


def test_load_api_roundtrip(file_data):
    session_response = client.post('/api/sessions', json={'label': 'Load API test'})
    assert session_response.status_code == 200
    session_id = session_response.json()['session_id']

    open_response = client.post(f'/api/sessions/{session_id}/load/open', json={'vendor_type': 1})
    assert open_response.status_code == 200
    assert 'cwd' in open_response.json()

    preview_response = client.post(
        f'/api/sessions/{session_id}/load/select-path',
        json={'path': str(data_path), 'vendor_type': 1},
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload['mode'] == 'file_loaded'
    assert preview_payload['preview']['source_path'] == str(data_path)
    assert isinstance(preview_payload['preview']['selected_signals'], list)
    assert preview_payload['preview']['figure']['data'][0]['name'] == RAW_EIT_LABEL

    confirm_response = client.post(
        f'/api/sessions/{session_id}/load/confirm',
        json={
            'relayout_data': {
                'xaxis.range': [file_data.time[FIRST_SAMPLE], file_data.time[LAST_SAMPLE]],
            },
            'selected_signals': [],
            'custom_name': None,
        },
    )
    assert confirm_response.status_code == 200
    datasets = confirm_response.json()['datasets']
    assert len(datasets) == 1
    rows = {row['label']: row['value'] for row in datasets[0]['rows']}
    assert rows['Name'] == data_path.name
    assert rows['Signals'] == RAW_EIT_LABEL
    assert rows['Path'] == str(data_path)

    delete_response = client.delete(f'/api/sessions/{session_id}/load/datasets/{data_path.name}')
    assert delete_response.status_code == 200
    assert delete_response.json()['datasets'] == []
