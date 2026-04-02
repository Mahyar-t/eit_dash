## EIT Dashboard

Visualize and manipulate EIT in a code free way using the open source
[eitprocessing](https://github.com/EIT-ALIVE/eitprocessing) software.

This repository currently contains two application entry points:

- the original Dash application
- the newer React + Vite frontend with a FastAPI backend that restores the three-step workflow for loading, preprocessing, and analysis

**Important:** While the software code is open source, your data may not be. Once the dashboard is downloaded (and/or
updated) on your local machine, no online interaction is needed. Your data remains local and is not shared or uploaded by
this software.

| Badges             |                                                                                                                                                                                                                                                |
| :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| code repository    | [![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](git@github.com:EIT-ALIVE/eit_dash)                                                                                             |
| license            | [![github license badge](https://img.shields.io/github/license/EIT-ALIVE/eit_dash)](git@github.com:EIT-ALIVE/eit_dash)                                                                                                                         |
| community registry | [![RSD](https://img.shields.io/badge/rsd-eit_dash-00a3e3.svg)](https://www.research-software.nl/software/eit_dash) [![workflow pypi badge](https://img.shields.io/pypi/v/eit_dash.svg?colorB=blue)](https://pypi.python.org/project/eit_dash/) |
| howfairis          | [![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)                                                                |
| Documentation      | [![Documentation Status](https://readthedocs.org/projects/eit_dash/badge/?version=latest)](https://eit_dash.readthedocs.io/en/latest/?badge=latest)                                                                                            |

## Getting started

##### Install EIT Dashboard

The first time that the dashboard is used, the repository needs to be cloned and the Python package has to be
installed locally as follows:

- Create fresh environment
  - Make sure you are in your base environment: `conda activate`
  - Create a new environment: `conda create -n <envname> python=3.10`
  - Activate new environment: `conda activate <envname>`
- Clone and install
  - Clone the repository: `git clone git@github.com:EIT-ALIVE/eit_dash.git`
  - Install:
    - Run `pip install -e .`

If you prefer explicit requirement files instead of an editable install:

```console
pip install -r requirements.txt
```

### 2. Running EIT Dashboard

##### Run the original Dash application

To run the original Dash dashboard the following command can be used::

```console
eit-dash run
```

Open the resulting link in a browser (often something like `http://127.0.0.1:8050/`).
Note that while the dashboard should work on any browser, if you are experiencing issues we recommend switching to
Chrome or Firefox, as these are the browser where we do most of the testing.

##### Run the new web application

The new web application uses:

- a FastAPI backend for workflow/session APIs
- a React + Vite frontend for the user interface

Start the backend from the repository root:

```console
eit-dash run-api
```

Then start the frontend in a second terminal:

```console
cd frontend
npm install
npm run dev
```

Open the Vite link shown in the terminal, usually `http://127.0.0.1:5173/`.

Please see our [user manual](docs/user_manual.md) for instructions on how to use the dashboard and [docs/web_preview.md](docs/web_preview.md) for details on the new web stack.

## For developers

### 1. Installation

##### Install Poetry

EIT Dashboard uses of [poetry](https://python-poetry.org/) to easily manage the needed packages.
Poetry can be installed as follows. Please refer to the [official installation instructions](https://python-poetry.org/docs/#installation) if problems arise:

In Linux (and WSL) or macOS

```console
curl -sSL https://install.python-poetry.org | python3 -
```

Alternatively, you can use Homebrew in macOS:

```console
brew install poetry
```

In Windows (using PowerShell)

```console
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Alternatively, poetry can also be installed [using pip](https://pypi.org/project/poetry/) or [conda](https://anaconda.org/conda-forge/poetry) in a virtual environment of choice.

##### Install EIT Dashboard

The first time that the dashboard is used, the repository needs to be cloned and the needed dependencies have to be
installed by navigating to the path where it should be installed and running:

```console
git clone git@github.com:EIT-ALIVE/eit_dash.git
cd eit_dash
poetry install
```

If you want the pip-based equivalent instead of Poetry:

```console
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

For the frontend:

```console
cd frontend
npm install
```

### 2. Running EIT Dashboard

##### Stay up to date

To ensure you are using the newest version, including any updates since you last used it, navigate to the folder where
the dashboard is installed and run:

```console
git pull
poetry install
```

##### Run the Dash application

Run the command below to run the dashboard with the latest change made in the code,
and follow the link displayed.

```console
poetry run eit-dash run
```

##### Run the new web stack

The React + Vite frontend and FastAPI backend now restore the three-step workflow for loading, preprocessing, and analysis while reusing the existing Python logic behind those stages.

```console
poetry run eit-dash run-api
cd frontend
npm install
npm run dev
```

See [docs/web_preview.md](docs/web_preview.md) for details.

## Documentation

- User guide: [docs/user_manual.md](docs/user_manual.md)
- Web stack notes: [docs/web_preview.md](docs/web_preview.md)

## Contributing

If you want to contribute to the development of eit_dash,
have a look at the [contribution guidelines](CONTRIBUTING.md).

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).

## License

This source code is licensed using a standard [Apache 2.0 License](LICENSE)
