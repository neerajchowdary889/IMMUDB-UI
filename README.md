# IMMUDB‑UI

I got so fed up with using ImmuDB due to its lack of proper documentation and a UI like MongoDB for key-value pair transactions. But for god’s sake, our blockchain *needs* ImmuDB. So, I built my own ImmuDB dashboard using Streamlit and the Python ImmuDB client library to explore data in an ImmuDB instance. It supports:

- Viewing all key‑value transaction
- Filtering by key prefix or suffix
- Displaying database Merkle root
- Exporting data as JSON

---

## Features

- Connect to any ImmuDB server & database
- Fetch and decode arbitrary keys & values
- Filter transactions by prefix or suffix
- Compute and display transaction count, key/value statistics
- Interactive Streamlit UI with expandable key/value view
- Download full or filtered results as JSON

---

## Prerequisites

- Python 3.8+
- ImmuDB server running (default port 3322)
- `immudb` Python client
- Streamlit and visualization libs

---

## Installation

```bash
git clone
cd IMMUDB‑UI

# Create & activate a virtualenv (optional)
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install immudb-py streamlit pandas plotly
```

---

## Configuration

Edit the connection settings in app.py sidebar or pass your server URL and database name when using the helper functions:

- URL format: `host:port` (e.g. `localhost:3322`)
- Default credentials: `username="immudb"`, `password="immudb"`

---

## Python Client Library

All ImmuDB operations are in Ops.py.

### ImmuDBReader

```python
from Operations.Ops import ImmuDBReader

reader = ImmuDBReader("localhost:3322", "defaultdb").connect()
all_data = reader.get_all_transactions()
prefix_data = reader.get_by_prefix("block:")
suffix_data = reader.get_by_suffix("hash")
root_info = reader.get_merkle_root()
```

- `get_all_transactions()` → `Dict[str, str]`
- `get_by_prefix(prefix: str)` → `Dict[str, str]`
- `get_by_suffix(suffix: str)` → `Dict[str, str]`
- `get_merkle_root()` → `{"txId": int, "merkleRoot": hex‑string}`

### Helper Functions

```python
from Operations.Ops import read_transactions, get_merkle_root

# Read optionally with prefix/suffix filters
data = read_transactions("localhost:3322", "defaultdb", prefix="block:")
root = get_merkle_root("localhost:3322", "defaultdb")
```

- `read_transactions(url, db_name, prefix=None, suffix=None)`
- `get_merkle_root(url, db_name)`

Also available:

- `get_transactions_as_json(...)`
- `get_merkle_root_as_json(...)`

---

## Streamlit Dashboard

Launch the interactive UI:

```bash
streamlit run app.py
```

**Sidebar**

- Enter ImmuDB URL & database name
- Click **Connect**
- View Merkle root & quick stats

**Tabs**

1. **Dashboard** – overview charts & stats
2. **All Transactions** – list & download
3. **Search by Prefix** – filter & download
4. **Search by Suffix** – filter & download
5. **About** – project information

Values that parse as JSON will render with `st.json()`, others display as plain text.

---
