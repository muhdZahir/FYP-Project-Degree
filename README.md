# URO: University Resource Optimization

## What it is

A Streamlit web app that reads classroom usage and energy/electrical cost data, shows charts, and gives suggestions to save cost. Built as a Final Year Project.

## Requirements

- Python 3.12
- pip

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`. To stop it, press `Ctrl + C` in the terminal.

## Login (demo accounts)

Login is hardcoded in `main.py`. Two roles:

| Role     | Username | Password    |
| -------- | -------- | ----------- |
| IT Staff | `staff`  | `1234staff` |
| Manager  | `admin`  | `4321admin` |

## How to use

### IT Staff

1. Go to **Upload Files**.
2. Upload one classroom file and one energy file (CSV or XLSX).
3. Enter a **Batch Name** in the format `Sem X YYYY` (example: `Sem 1 2024`).
4. Click **Save Data**.
5. Use **Manage Data** to rename a batch or delete records.

### Manager

1. Pick a batch from the sidebar dropdown, then click **Load Data**.
2. **View Data** — see the raw records.
3. **Analysis** — charts and findings (worst rooms, heatmap, monthly cost, pie, correlation).
4. **Optimization** — predictions and action plan.

## Data format

### Classroom file columns

`Classroom_ID`, `Floor`, `Capacity`, `Scheduled_Hours`, `Actual_Occupancy`, `Day`, `Time_Slot`, `Week`

Example:

| Classroom_ID | Floor | Capacity | Scheduled_Hours | Actual_Occupancy | Day | Time_Slot   | Week |
| ------------ | ----- | -------- | --------------- | ---------------- | --- | ----------- | ---- |
| 1901         | 19    | 30       | 2               | 17               | Mon | 10:00-12:00 | 4    |
| 802          | 8     | 40       | 2               | 34               | Thu | 14:00-16:00 | 7    |

### Energy file columns

`Floor`, `Month`, `Energy_kWh`, `Energy_Cost`

Example:

| Floor | Month | Energy_kWh | Energy_Cost |
| ----- | ----- | ---------- | ----------- |
| 1     | Feb   | 1023       | 657         |
| 4     | Mar   | 894        | 454         |

The system cleans the data automatically (drops missing values, invalid days, invalid time slots, duplicates, etc.).

## Project layout

```
FYP-Project-Degree/
├── main.py                # Entry point: login, navigation, session state
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml        # Theme + sidebar settings
├── assets/
│   ├── style.css
│   └── URO_logo.png
├── core/
│   ├── imports.py         # Central library imports
│   ├── database.py        # SQLite read/write
│   ├── processing.py      # Data cleaning + aggregation
│   ├── visualization.py   # Plotly charts
│   └── insights.py        # Text findings
├── database/
│   └── uro_system.db      # SQLite file (demo data)
└── pages/
    ├── dashboard.py
    ├── upload.py
    ├── manage.py
    ├── view.py
    ├── analysis.py
    └── optimize.py
```

## Known limitations

- Login is hardcoded in `main.py`. Replace this before deploying to a real environment.
- Analysis and Optimization pages assume there are at least 2 rooms and at least 2 months of data. Very small datasets can crash the page.
- The database file `database/uro_system.db` is included so the app works out of the box. Delete it if you want a fresh install.
