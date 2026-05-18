# U2RZ Inventory Management

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)
![Tested on TestGrid](https://img.shields.io/badge/Tested%20on-TestGrid%20Device%20Cloud-0057FF)

A Streamlit-based inventory management application for tracking product expiry dates and stock counts across a retail store. The app integrates with MongoDB Atlas and supports EAN barcode scanning directly from a device camera.

---

## Features

- **EAN Barcode Scanning** — Built-in HTML5 QR/barcode scanner using the device camera. Scan a product EAN and auto-populate all product details from the master inventory.
- **Dual Tracking Mode** — Record products either for expiry date tracking or stock count tracking, stored in separate MongoDB collections.
- **Database Management** — Update or delete individual records, or bulk-delete by segment or class.
- **Scanning Progress Dashboard** — Visualise what percentage of inventory has been scanned per segment or family, with a breakdown of remaining products.
- **Near Expiry Alerts** — Filter and display products expiring within 15, 20, or 30 days.
- **Raw Data Export** — View and filter the full scanned dataset by segment or family.
- **Password-Protected Dashboard** — Analytics are gated behind a configurable password stored in Streamlit secrets.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io) |
| Barcode Scanning | [html5-qrcode](https://github.com/mebjas/html5-qrcode) (CDN) |
| Database | [MongoDB Atlas](https://www.mongodb.com/atlas) via PyMongo |
| Visualisation | [Plotly Express](https://plotly.com/python/plotly-express/) |
| Language | Python 3.11 |
| Hosting | GitHub Codespaces / any Streamlit-compatible host |

---

## Project Structure

```
.
├── expiry_notifier.py          # Main application
├── requirements.txt            # Python dependencies
├── packages.txt                # System-level apt packages (for Codespaces)
├── .streamlit/
│   └── secrets.toml.example   # Secrets template — copy and fill before running
├── .devcontainer/
│   └── devcontainer.json       # GitHub Codespaces configuration
└── data/
    └── U2RZ_inventory_csv.csv  # Master product catalogue (EAN reference data)
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A MongoDB Atlas cluster with three collections: `Inventory`, `Products`, `Product_count`
- The `Inventory` collection pre-populated from `data/U2RZ_inventory_csv.csv`

### Installation

```bash
git clone https://github.com/jay6430/U2RZ-Inventory-Management.git
cd U2RZ-Inventory-Management
pip install -r requirements.txt
```

### Configuration

The app reads credentials from Streamlit secrets. Create `.streamlit/secrets.toml` based on the provided template:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and fill in your values:

```toml
MONGO_URI = "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority"
DASHBOARD_PASSWORD = "your_secure_dashboard_password"
```

> **Important:** `secrets.toml` is listed in `.gitignore` and must never be committed to version control.

### Running Locally

```bash
streamlit run expiry_notifier.py
```

The app opens at `http://localhost:8501`.

### Running in GitHub Codespaces

Open the repository in a Codespace. The `.devcontainer` configuration installs all dependencies and starts the Streamlit server automatically on port 8501.

---

## MongoDB Collections

| Collection | Purpose |
|---|---|
| `Inventory` | Master product catalogue — EAN, article number, segment, family, class |
| `Products` | Scanned products with expiry dates |
| `Product_count` | Scanned products with stock counts |

---

## Application Pages

### Add Product
Scan or manually enter a product EAN to look it up in the master inventory. Product details are auto-filled. Choose to record the product for expiry tracking or stock count tracking.

### Modify Database
Select a record to update its fields, or delete records individually, by segment, or by class. Separate tabs handle the expiry and count collections independently.

### Dashboard *(password protected)*
- **Expiry / Count Scanning Status** — Pie charts showing scanned vs. remaining products for a selected segment or family, with a table of unscanned items.
- **Near Expiry Dashboard** — Lists all products expiring within a configurable window (15 / 20 / 30 days).
- **Raw Data** — Full table view of either collection, filterable by segment or family.

This web app was tested using [TestGrid](https://testgrid.io). 

---

## License

This project is provided for internal use. No open-source license is currently applied.
