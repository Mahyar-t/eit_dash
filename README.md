## EIT Dashboard

Visualize and manipulate EIT data in a code-free way using the open source
[eitprocessing](https://github.com/EIT-ALIVE/eitprocessing) software.

EIT Dashboard is a local web application with:

- a FastAPI backend for workflow and session APIs
- a React + Vite frontend for loading, preprocessing, and analysis
- Python processing logic reused behind the workflow steps

**Important:** While the software code is open source, your data may not be. Once the dashboard is downloaded and
updated on your local machine, no online interaction is needed. Your data remains local and is not shared or uploaded by
this software.

| Badges             |                                                                                                                                                                                                                                                |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| code repository    | [![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](git@github.com:EIT-ALIVE/eit_dash)                                                                                             |
| license            | [![github license badge](https://img.shields.io/github/license/EIT-ALIVE/eit_dash)](git@github.com:EIT-ALIVE/eit_dash)                                                                                                                         |
| community registry | [![RSD](https://img.shields.io/badge/rsd-eit_dash-00a3e3.svg)](https://www.research-software.nl/software/eit_dash) [![workflow pypi badge](https://img.shields.io/pypi/v/eit_dash.svg?colorB=blue)](https://pypi.python.org/project/eit_dash/) |
| howfairis          | [![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)                                                                |
| Documentation      | [![Documentation Status](https://readthedocs.org/projects/eit_dash/badge/?version=latest)](https://eit_dash.readthedocs.io/en/latest/?badge=latest)                                                                                            |

## Getting Started

### Install EIT Dashboard

The first time you use the dashboard, clone the repository and install the Python package in your environment.

If you use conda, create and activate an environment first:

```console
conda create -n eit_dash python=3.10
conda activate eit_dash
```

If you already have a conda environment, activate that environment instead:

```console
conda activate <envname>
```

Then clone and install the package from the repository root:

```console
git clone git@github.com:EIT-ALIVE/eit_dash.git
cd eit_dash
python -m pip install -e .
```

If you prefer explicit requirement files instead of an editable install:

```console
python -m pip install -r requirements.txt
```

Install the frontend dependencies from the `frontend` folder:

```console
cd frontend
npm install
```

### Run EIT Dashboard

The dashboard has two parts that must run at the same time. Use two separate terminals.

In each terminal, first move into the cloned repository:

```console
cd path/to/eit_dash
```

Terminal 1: start the backend from the repository root:

```console
eit-dash-api
```

`eit-dash-api` starts the backend directly and does not go through the Dash CLI command.
If you are using conda and `eit-dash-api` is not found, make sure the package is installed in the active conda environment:

```console
conda activate <envname>
cd path/to/eit_dash
python -m pip install -e .
```

If a command still uses the wrong environment, run the backend module directly from the repository root:

```console
python -m backend
```

The backend should print a message like `Uvicorn running on http://127.0.0.1:8000`.
To check that it is running, open `http://127.0.0.1:8000/docs` in your browser.

Opening `http://127.0.0.1:8000/` returns `404 Not Found`. That is expected because the backend serves API routes, not the web page.

Terminal 2: start the frontend:

```console
cd frontend
npm install
npm run dev
```

Run `npm install` and `npm run dev` only after you have entered the `frontend` folder. You can check that you are in the right place by confirming that `package.json` exists:

```console
ls package.json
```

If you run `npm run dev` from the repository root, npm will fail with an error like `ENOENT: no such file or directory, open '.../eit_dash/package.json'`.

Open the Vite link shown in the frontend terminal, usually `http://127.0.0.1:5173/`.
If port `5173` is already in use, Vite will choose another port, such as `http://127.0.0.1:5174/`.

Keep both terminals running while you use the dashboard. Stop either process with `Ctrl+C`.

The dashboard should work in any modern browser. If you experience browser-specific issues, try Chrome or Firefox, which are the browsers used most often during testing.

Please see the [user manual](docs/user_manual.md) for instructions on how to use the dashboard and [docs/web_preview.md](docs/web_preview.md) for implementation notes.

## For Developers

### Install Poetry

EIT Dashboard uses [Poetry](https://python-poetry.org/) to manage Python packages for development.
Please refer to the [official installation instructions](https://python-poetry.org/docs/#installation) if problems arise.

On Linux, WSL, or macOS:

```console
curl -sSL https://install.python-poetry.org | python3 -
```

Alternatively, use Homebrew on macOS:

```console
brew install poetry
```

On Windows using PowerShell:

```console
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Poetry can also be installed [using pip](https://pypi.org/project/poetry/) or [conda](https://anaconda.org/conda-forge/poetry) in a virtual environment of your choice.

### Install Development Dependencies

Clone the repository and install the Python dependencies:

```console
git clone git@github.com:EIT-ALIVE/eit_dash.git
cd eit_dash
poetry install
```

If you want the pip-based equivalent instead of Poetry:

```console
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

If you use conda for development, activate your conda environment before installing:

```console
conda activate <envname>
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

Install the frontend dependencies:

```console
cd frontend
npm install
```

### Stay Up To Date

To ensure you are using the newest version, including any updates since you last used it, navigate to the folder where
the dashboard is installed and run:

```console
git pull
poetry install
cd frontend
npm install
```

### Run For Development

Run the backend and frontend in two separate terminals.

Terminal 1: start the backend from the repository root:

```console
poetry run eit-dash-api
```

If you are using conda instead of Poetry, run this from the repository root:

```console
eit-dash-api
```

If the console command is not available or your shell resolves the wrong command, run the backend module directly:

```console
python -m backend
```

The backend should be available at `http://127.0.0.1:8000/docs`.
Opening `http://127.0.0.1:8000/` returns `404 Not Found`, which is normal for the API server.

Terminal 2: start the frontend:

```console
cd frontend
npm run dev
```

Run the npm commands from inside the `frontend` folder. If you run `npm run dev` from the repository root, npm will fail because `package.json` is in `frontend/package.json`.

Open the Vite link shown in the frontend terminal, usually `http://127.0.0.1:5173/`.
If port `5173` is already in use, Vite will choose another port, such as `http://127.0.0.1:5174/`.
Keep both terminals running while you use the dashboard. Stop either process with `Ctrl+C`.

See [docs/web_preview.md](docs/web_preview.md) for implementation notes.

## Documentation

- User guide: [docs/user_manual.md](docs/user_manual.md)
- Implementation notes: [docs/web_preview.md](docs/web_preview.md)

## Contributing

If you want to contribute to the development of eit_dash,
have a look at the [contribution guidelines](CONTRIBUTING.md).

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).

## License

This source code is licensed using a standard [Apache 2.0 License](LICENSE)
