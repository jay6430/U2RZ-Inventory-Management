import streamlit as st
import pandas as pd
from pymongo import MongoClient, errors
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

MONGO_URI = st.secrets["MONGO_URI"]
DASHBOARD_PASSWORD = st.secrets["DASHBOARD_PASSWORD"]

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["expiry_notifier"]
    inventory_collection = db["Inventory"]
    products_collection = db["Products"]
    product_count_collection = db["Product_count"]
    client.server_info()
except errors.ServerSelectionTimeoutError as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop()


# ---------------------------------------------------------------------------
# Static lookup lists  (sourced from the master inventory CSV)
# ---------------------------------------------------------------------------

UNIQUE_SEGMENTS = [
    "PROCESSED FOOD", "FRAGRANCES", "CONFECTIONARY & SNACKS", "FURNISHINGS & DECOR",
    "STAPLES", "AUTO ACCESSORIES", "PERSONAL CARE", "STATIONERY", "BABY CARE",
    "HOME CARE", "HEALTH", "GM FMCG", "BEVERAGES", "FROZEN VEG. / SNACKS", "DAIRY",
    "HOUSEWARE", "TOYS", "CONSUMABLES", "FRESH FRUITS & VEGETABLES", "FURNITURE",
    "GIFT SOLUTIONS", "COSMETICS", "BEAUTY", "3902", "LUGGAGE",
    "CONCESSIONAIRE SERVICES", "SPORTING GOODS & FITNESS EQUIPMENTS", "Devices",
    "SERVICES", "HARDLINES",
]
UNIQUE_FAMILIES = [
    "BISCUITS & BRANDED BAKERY", "MASS MENS FRAGRANCE", "CONFECTIONERY", "FURNISHINGS",
    "SPICES & CONDIMENTS", "TWO WHEELER", "SKIN PRODUCTS", "WRITING INSTRUMENTS & ACCESSORIES",
    "READY TO EAT", "BABY HYGN", "FLOURS", "READY TO COOK", "PULSES", "HOUSEHOLD NEEDS",
    "OTC", "Pooja Needs", "RICE", "PAPER PRODUCTS", "FABRIC CARE", "SNACKS", "HAIR PRODUCTS",
    "TEA & COFFEE", "OFFICE CONSUMABLES & STATIONERY", "P'SONAL HYGN", "Hardlines", "SKIN CARE",
    "FROZEN SNACKS", "Disposable Goods", "DAIRY - STAPLE", "DRY FRUITS", "INSECT CONTROL",
    "HOUSEHOLD CLEANING", "DRINKS", "Home Essential", "Kitchen Storage", "SCHOOL & ART PRODUCTS",
    "TABLEWARE", "PERSONAL WASH", "JUICES", "H'HOLD CLNG/CARENG/CARE", "COOKWARE",
    "VEHICLES & ACCESSORIES", "EDIBLE OILS", "AYURVEDIC", "HEALTH DRINKS",
    "BRANDED BAKERY FRESH BAKERY", "FRESH MILK PRODUCTS", "SALT", "Bottle and lunch box",
    "OTHER TOYS", "DC / STORE CONSUMABLES", "FRESH FRUITS", "HOME DECOR", "PERSONAL HYGIENE",
    "DAIRY - CHILLED", "FROZEN FRUITS & VEGETABLES", "Deo", "GIFTS",
]
UNIQUE_CLASSES = [
    "BISCUITS", "BODY SPRAYS", "CONFECTIONERY", "TABLE & KITCHEN", "BLENDED SPICES",
    "POWDER SPICES", "SPICES HING", "SAFETY", "SKIN CARE", "PENS & ACCESSORIES",
    "JAMS & SPREADS", "BABY HYGN/GROOMING", "FLOURS", "BODY WASHING", "NOODLES & PASTA",
    "PULSES", "AIR FRESHNERS", "SKIN/SCALP TREATMENT PRODUCTS", "Incense & Dhoop",
    "SAUCES", "RICE", "GASTROINTESTINAL REMEDY PRODUCTS", "WHOLE SPICES", "NOTE BOOKS",
    "LAUNDRY DETERGENTS", "SNACKS", "DESSERTS & MIXES", "HAIR CARE", "TEA",
    "FOLDERS & ACCESSORIES", "ORAL HYGN", "Bonding & Sealing", "FACE CARE", "BAKERY BASED",
    "BREAKFAST CEREALS", "Face Tissues", "GHEE", "DRY FRUITS", "INSECT CONTROL PRODUCTS",
    "FEM HYGN", "HEALTH SUPPLEMENTS", "SURFACE CLEANING", "CARBONATED SOFT DRINKS",
]


# ---------------------------------------------------------------------------
# Barcode scanner component
# ---------------------------------------------------------------------------

BARCODE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html5-qrcode/2.3.8/html5-qrcode.min.js"></script>
</head>
<body style="font-family: Arial, sans-serif; background-color: #333; color: #f5f5f5;">
    <h4>Scan EAN Barcode</h4>
    <div style="display: flex; justify-content: center; margin-top: 20px;">
        <div id="reader" style="
            width: 500px;
            height: 450px;
            border: 5px solid white;
            border-radius: 10px;
            position: relative;
            background: black;">
        </div>
    </div>
    <div style="text-align: center; margin-top: 20px;">
        <h4>Scan Result</h4>
        <div id="result" style="
            padding: 15px;
            border: 2px solid #ccc;
            border-radius: 5px;
            background-color: #f5f5f5;
            color: #333;
            font-size: 18px;
            word-wrap: break-word;
            display: inline-block;">---   EAN   ---</div>
        <button id="copyEANButton" onclick="copyEAN()" style="
            padding: 10px 20px;
            margin-top: 10px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;">Copy EAN</button>
        <div id="copyMessage" style="
            margin-top: 10px;
            font-size: 14px;
            color: #4CAF50;
            display: none;">EAN copied to clipboard!</div>
    </div>
    <script>
        function onScanSuccess(qrCodeMessage) {
            document.getElementById("reader").style.border = "5px solid green";
            document.getElementById("result").innerHTML = "<span>" + qrCodeMessage + "</span>";
        }

        function onScanError(errorMessage) {
            console.warn("Scan error:", errorMessage);
        }

        const html5QrCodeScanner = new Html5QrcodeScanner("reader", {
            fps: 10,
            qrbox: { width: 250, height: 200 }
        });
        html5QrCodeScanner.render(onScanSuccess, onScanError);

        function copyEAN() {
            const ean = document.getElementById("result").innerText;
            const copyMessage = document.getElementById("copyMessage");
            if (ean) {
                navigator.clipboard.writeText(ean).then(function () {
                    copyMessage.style.color = "#4CAF50";
                    copyMessage.innerText = "EAN copied to clipboard!";
                    copyMessage.style.display = "block";
                    setTimeout(() => { copyMessage.style.display = "none"; }, 2000);
                }).catch(function () {
                    copyMessage.style.color = "red";
                    copyMessage.innerText = "Failed to copy EAN!";
                    copyMessage.style.display = "block";
                    setTimeout(() => { copyMessage.style.display = "none"; }, 2000);
                });
            }
        }
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def load_products_from_products_collection():
    """Return all records from the Products (expiry) collection."""
    try:
        return list(products_collection.find({}, {"_id": 0}))
    except Exception as e:
        st.error(f"Error loading products: {e}")
        return []


def load_products_from_product_count_collection():
    """Return all records from the Product_count collection."""
    try:
        return list(product_count_collection.find({}, {"_id": 0}))
    except Exception as e:
        st.error(f"Error loading product counts: {e}")
        return []


def add_product(data, collection):
    """Insert a new product record into the given collection."""
    try:
        collection.insert_one(data)
    except Exception as e:
        st.error(f"Error adding product: {e}")


def fetch_inventory_details(ean):
    """Return the Inventory document matching the given EAN, or None."""
    try:
        return inventory_collection.find_one({"EAN": ean}, {"_id": 0})
    except Exception as e:
        st.error(f"Error fetching inventory details: {e}")
        return None


def get_unique_values_product_collection(field):
    """Return sorted unique values for a field in the Products collection."""
    try:
        return sorted({rec.get(field, "") for rec in products_collection.find({}, {field: 1, "_id": 0})})
    except Exception as e:
        st.error(f"Error fetching unique {field}s: {e}")
        return []


def get_unique_values_product_count_collection(field):
    """Return sorted unique values for a field in the Product_count collection."""
    try:
        return sorted({rec.get(field, "") for rec in product_count_collection.find({}, {field: 1, "_id": 0})})
    except Exception as e:
        st.error(f"Error fetching unique {field}s: {e}")
        return []


def fetch_inventory_for_value(field, value):
    """Return EAN and description records from Inventory matching a field/value."""
    try:
        return list(inventory_collection.find(
            {field: value},
            {"EAN": 1, "Material_description": 1, "_id": 0},
        ))
    except Exception as e:
        st.error(f"Error fetching inventory for {field} '{value}': {e}")
        return []


def fetch_products_for_value(field, value):
    """Return EAN_No and product_name records from Products matching a field/value."""
    try:
        return list(products_collection.find(
            {field: value},
            {"EAN_No": 1, "product_name": 1, "_id": 0},
        ))
    except Exception as e:
        st.error(f"Error fetching products for {field} '{value}': {e}")
        return []


def fetch_products_count_for_value(field, value):
    """Return EAN_No and product_name records from Product_count matching a field/value."""
    try:
        return list(product_count_collection.find(
            {field: value},
            {"EAN_No": 1, "product_name": 1, "_id": 0},
        ))
    except Exception as e:
        st.error(f"Error fetching product counts for {field} '{value}': {e}")
        return []


def compute_scanning_status(inventory_data, scanned_data):
    """Return (scanned_pct, remaining_pct, remaining_items) for pie-chart display."""
    inventory_eans = {inv["EAN"] for inv in inventory_data}
    scanned_eans = {prod["EAN_No"] for prod in scanned_data}
    total = len(inventory_eans)
    scanned = len(scanned_eans & inventory_eans)
    remaining_items = [inv for inv in inventory_data if inv["EAN"] not in scanned_eans]
    scanned_pct = (scanned / total * 100) if total > 0 else 0
    return scanned_pct, 100 - scanned_pct, remaining_items


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "Add Product"
if "product_details" not in st.session_state:
    st.session_state.product_details = {
        "product_name": "",
        "article_num": "",
        "segment": "",
        "family": "",
        "prod_class": "",
    }


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("U2RZ Navigation")
st.sidebar.caption("Manage your inventory with ease.")

PAGE_LABELS = {
    "Add Product": "Add Product",
    "Modify Database": "Modify Database",
    "Dashboard": "Dashboard",
}

selected_label = st.sidebar.radio(
    "Navigation",
    list(PAGE_LABELS.values()),
    index=list(PAGE_LABELS.keys()).index(st.session_state.page),
    key="sidebar_navigation",
)
st.session_state.page = list(PAGE_LABELS.keys())[list(PAGE_LABELS.values()).index(selected_label)]


# ===========================================================================
# Page: Add Product
# ===========================================================================

if st.session_state.page == "Add Product":
    st.title("U2RZ Inventory Management")
    st.subheader("Add Product")

    components.html(BARCODE_HTML, height=730)

    with st.form("fetch_details_form"):
        ean_no = st.text_input("Product EAN Number", key="ean_input", placeholder="Enter or scan EAN")
        if st.form_submit_button("Fetch Details"):
            if ean_no:
                details = fetch_inventory_details(ean_no)
                if details:
                    st.session_state.product_details.update({
                        "product_name": details.get("Material_description", ""),
                        "article_num": details.get("Article_num", ""),
                        "segment": details.get("Segment", ""),
                        "family": details.get("Family", ""),
                        "prod_class": details.get("Class", ""),
                    })
                    st.success("Details fetched successfully.")
                else:
                    st.warning("EAN not found in the inventory.")
            else:
                st.warning("Please enter a valid EAN number.")

    tab1, tab2 = st.tabs(["Add Product for Expiry", "Add Product for Count"])

    with tab1:
        st.subheader("Add Product for Expiry")
        with st.form("add_product_form", clear_on_submit=True):
            product_name = st.text_input(
                "Product Name",
                value=st.session_state.product_details.get("product_name", ""),
                placeholder="Mandatory",
            )
            article_num = st.text_input(
                "Article Number",
                value=st.session_state.product_details.get("article_num", ""),
                placeholder="Optional",
            )
            segment = st.selectbox(
                "Segment",
                options=[st.session_state.product_details.get("segment", "")] + UNIQUE_SEGMENTS,
            )
            family = st.selectbox(
                "Family",
                options=[st.session_state.product_details.get("family", "")] + UNIQUE_FAMILIES,
            )
            prod_class = st.selectbox(
                "Class",
                options=[st.session_state.product_details.get("prod_class", "")] + UNIQUE_CLASSES,
            )
            expiry_date = st.date_input("Expiry Date")

            if st.form_submit_button("Add Product"):
                if product_name and expiry_date:
                    add_product(
                        {
                            "EAN_No": ean_no,
                            "product_name": product_name,
                            "article_number": article_num or None,
                            "segment": segment or None,
                            "family": family or None,
                            "class": prod_class or None,
                            "expiry_date": expiry_date.strftime("%d/%m/%Y"),
                            "timestamp": datetime.now(),
                        },
                        products_collection,
                    )
                    st.success("Product added successfully.")
                else:
                    st.error("Please fill in all mandatory fields.")

    with tab2:
        st.subheader("Add Product for Count")
        with st.form("add_product_count_form", clear_on_submit=True):
            product_name = st.text_input(
                "Product Name",
                value=st.session_state.product_details.get("product_name", ""),
                placeholder="Mandatory",
            )
            article_num = st.text_input(
                "Article Number",
                value=st.session_state.product_details.get("article_num", ""),
                placeholder="Optional",
            )
            segment = st.selectbox(
                "Segment",
                options=[st.session_state.product_details.get("segment", "")] + UNIQUE_SEGMENTS,
            )
            family = st.selectbox(
                "Family",
                options=[st.session_state.product_details.get("family", "")] + UNIQUE_FAMILIES,
            )
            prod_class = st.selectbox(
                "Class",
                options=[st.session_state.product_details.get("prod_class", "")] + UNIQUE_CLASSES,
            )
            product_count = st.number_input("Product Count", min_value=0, value=0)

            if st.form_submit_button("Add Product"):
                if product_name:
                    add_product(
                        {
                            "EAN_No": ean_no,
                            "product_name": product_name,
                            "article_number": article_num or None,
                            "segment": segment or None,
                            "family": family or None,
                            "class": prod_class or None,
                            "product_count": product_count,
                            "timestamp": datetime.now(),
                        },
                        product_count_collection,
                    )
                    st.success("Product count added successfully.")
                else:
                    st.error("Please fill in all mandatory fields.")


# ===========================================================================
# Page: Modify Database
# ===========================================================================

elif st.session_state.page == "Modify Database":
    st.title("Modify Database")

    tab1, tab2 = st.tabs(["Modify Database for Product Expiry", "Modify Database for Product Count"])

    def _build_dropdown(records):
        options = [
            {
                "EAN_No": rec["EAN_No"],
                "product_name": rec["product_name"],
                "record": rec,
                "display": f"{rec['EAN_No']} - {rec['product_name']}",
            }
            for rec in records
        ]
        return options, [o["display"] for o in options]

    with tab1:
        operation = st.radio(
            "Select operation:",
            ["Update Record", "Delete Single/Multiple Records", "Delete Entire Segment", "Delete Entire Class"],
            key="op_expiry",
        )
        records = load_products_from_products_collection()

        if records:
            options, labels = _build_dropdown(records)

            if operation == "Update Record":
                sel_label = st.selectbox("Select a record to update", labels, key="upd_sel_expiry")
                sel_rec = next(o["record"] for o in options if o["display"] == sel_label)

                updated = {
                    "EAN_No": st.text_input("EAN", value=sel_rec["EAN_No"], key="upd_ean_expiry"),
                    "product_name": st.text_input("Product Name", value=sel_rec["product_name"], key="upd_name_expiry"),
                    "article_number": st.text_input("Article Number", value=sel_rec.get("article_number", ""), key="upd_art_expiry"),
                    "segment": st.text_input("Segment", value=sel_rec.get("segment", ""), key="upd_seg_expiry"),
                    "family": st.text_input("Family", value=sel_rec.get("family", ""), key="upd_fam_expiry"),
                    "class": st.text_input("Class", value=sel_rec.get("class", ""), key="upd_cls_expiry"),
                    "expiry_date": st.date_input(
                        "Expiry Date",
                        value=datetime.strptime(sel_rec["expiry_date"], "%d/%m/%Y"),
                        key="upd_exp_expiry",
                    ),
                }
                updated["expiry_date"] = updated["expiry_date"].strftime("%d/%m/%Y")

                if st.button("Modify Record", key="btn_modify_expiry"):
                    try:
                        products_collection.update_one(
                            {"EAN_No": sel_rec["EAN_No"]},
                            {"$set": updated},
                        )
                        st.success("Record updated successfully.")
                    except Exception as e:
                        st.error(f"Error updating record: {e}")

            elif operation == "Delete Single/Multiple Records":
                sel_labels = st.multiselect("Select records to delete", labels, key="del_multi_expiry")
                sel_recs = [o["record"] for o in options if o["display"] in sel_labels]

                if sel_recs and st.button("Delete Selected Record(s)", key="btn_del_expiry"):
                    try:
                        products_collection.delete_many(
                            {"$or": [{"EAN_No": r["EAN_No"]} for r in sel_recs]}
                        )
                        st.success("Selected records deleted successfully.")
                    except Exception as e:
                        st.error(f"Error deleting records: {e}")

            elif operation == "Delete Entire Segment":
                segs = sorted({r.get("segment", "") for r in records if r.get("segment")})
                sel_seg = st.selectbox("Select a segment to delete", segs, key="del_seg_expiry")
                if sel_seg and st.button("Delete Segment", key="btn_del_seg_expiry"):
                    try:
                        products_collection.delete_many({"segment": sel_seg})
                        st.success(f"All records under segment '{sel_seg}' deleted.")
                    except Exception as e:
                        st.error(f"Error deleting segment: {e}")

            elif operation == "Delete Entire Class":
                classes = sorted({r.get("class", "") for r in records if r.get("class")})
                sel_cls = st.selectbox("Select a class to delete", classes, key="del_cls_expiry")
                if sel_cls and st.button("Delete Class", key="btn_del_cls_expiry"):
                    try:
                        products_collection.delete_many({"class": sel_cls})
                        st.success(f"All records under class '{sel_cls}' deleted.")
                    except Exception as e:
                        st.error(f"Error deleting class: {e}")
        else:
            st.warning("No records found in the database.")

    with tab2:
        operation = st.radio(
            "Select operation:",
            ["Update Record", "Delete Single/Multiple Records", "Delete Entire Segment", "Delete Entire Class"],
            key="op_count",
        )
        records = load_products_from_product_count_collection()

        if records:
            options, labels = _build_dropdown(records)

            if operation == "Update Record":
                sel_label = st.selectbox("Select a record to update", labels, key="upd_sel_count")
                sel_rec = next(o["record"] for o in options if o["display"] == sel_label)

                updated = {
                    "EAN_No": st.text_input("EAN", value=sel_rec["EAN_No"], key="upd_ean_count"),
                    "product_name": st.text_input("Product Name", value=sel_rec["product_name"], key="upd_name_count"),
                    "article_number": st.text_input("Article Number", value=sel_rec.get("article_number", ""), key="upd_art_count"),
                    "segment": st.text_input("Segment", value=sel_rec.get("segment", ""), key="upd_seg_count"),
                    "family": st.text_input("Family", value=sel_rec.get("family", ""), key="upd_fam_count"),
                    "class": st.text_input("Class", value=sel_rec.get("class", ""), key="upd_cls_count"),
                    "product_count": st.number_input(
                        "Product Count",
                        min_value=0,
                        value=int(sel_rec.get("product_count", 0)),
                        key="upd_cnt_count",
                    ),
                }

                if st.button("Modify Record", key="btn_modify_count"):
                    try:
                        product_count_collection.update_one(
                            {"EAN_No": sel_rec["EAN_No"]},
                            {"$set": updated},
                        )
                        st.success("Record updated successfully.")
                    except Exception as e:
                        st.error(f"Error updating record: {e}")

            elif operation == "Delete Single/Multiple Records":
                sel_labels = st.multiselect("Select records to delete", labels, key="del_multi_count")
                sel_recs = [o["record"] for o in options if o["display"] in sel_labels]

                if sel_recs and st.button("Delete Selected Record(s)", key="btn_del_count"):
                    try:
                        product_count_collection.delete_many(
                            {"$or": [{"EAN_No": r["EAN_No"]} for r in sel_recs]}
                        )
                        st.success("Selected records deleted successfully.")
                    except Exception as e:
                        st.error(f"Error deleting records: {e}")

            elif operation == "Delete Entire Segment":
                segs = sorted({r.get("segment", "") for r in records if r.get("segment")})
                sel_seg = st.selectbox("Select a segment to delete", segs, key="del_seg_count")
                if sel_seg and st.button("Delete Segment", key="btn_del_seg_count"):
                    try:
                        product_count_collection.delete_many({"segment": sel_seg})
                        st.success(f"All records under segment '{sel_seg}' deleted.")
                    except Exception as e:
                        st.error(f"Error deleting segment: {e}")

            elif operation == "Delete Entire Class":
                classes = sorted({r.get("class", "") for r in records if r.get("class")})
                sel_cls = st.selectbox("Select a class to delete", classes, key="del_cls_count")
                if sel_cls and st.button("Delete Class", key="btn_del_cls_count"):
                    try:
                        product_count_collection.delete_many({"class": sel_cls})
                        st.success(f"All records under class '{sel_cls}' deleted.")
                    except Exception as e:
                        st.error(f"Error deleting class: {e}")
        else:
            st.warning("No records found in the database.")


# ===========================================================================
# Page: Dashboard
# ===========================================================================

elif st.session_state.page == "Dashboard":
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Authentication Required")
        with st.form("login_form"):
            password = st.text_input("Enter Password:", type="password")
            if st.form_submit_button("Login"):
                if password == DASHBOARD_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("Authentication successful.")
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")

    else:
        st.title("Dashboard")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Expiry Products Scanning Status",
            "Product Count Scanning Status",
            "Near Expiry Dashboard",
            "Raw Data",
        ])

        with tab1:
            st.subheader("Expiry Products Scanning Status")
            dash_type = st.radio("Select view:", ["Segment", "Family"], key="dash_type_expiry")

            if dash_type == "Segment":
                segments = get_unique_values_product_collection("segment")
                sel = st.selectbox("Select Segment", segments, key="expiry_seg_sel")
                if sel:
                    inv = fetch_inventory_for_value("Segment", sel)
                    prods = fetch_products_for_value("segment", sel)
                    sc_pct, rem_pct, remaining = compute_scanning_status(inv, prods)
                    fig = px.pie(
                        names=["Scanned", "Remaining"],
                        values=[sc_pct, rem_pct],
                        title=f"Scanned vs Remaining — {sel}",
                        hole=0.3,
                    )
                    st.plotly_chart(fig, key="expiry_seg_chart")
                    if remaining:
                        st.write(f"**Remaining products in {sel}**")
                        st.dataframe(pd.DataFrame(remaining))
                    else:
                        st.info(f"All products in segment '{sel}' have been scanned.")

            elif dash_type == "Family":
                families = get_unique_values_product_collection("family")
                sel = st.selectbox("Select Family", families, key="expiry_fam_sel")
                if sel:
                    inv = fetch_inventory_for_value("Family", sel)
                    prods = fetch_products_for_value("family", sel)
                    sc_pct, rem_pct, remaining = compute_scanning_status(inv, prods)
                    fig = px.pie(
                        names=["Scanned", "Remaining"],
                        values=[sc_pct, rem_pct],
                        title=f"Scanned vs Remaining — {sel}",
                        hole=0.3,
                    )
                    st.plotly_chart(fig, key="expiry_fam_chart")
                    if remaining:
                        st.write(f"**Remaining products in {sel}**")
                        st.dataframe(pd.DataFrame(remaining))
                    else:
                        st.info(f"All products in family '{sel}' have been scanned.")

        with tab2:
            st.subheader("Product Count Scanning Status")
            dash_type = st.radio("Select view:", ["Segment", "Family"], key="dash_type_count")

            if dash_type == "Segment":
                segments = get_unique_values_product_count_collection("segment")
                sel = st.selectbox("Select Segment", segments, key="count_seg_sel")
                if sel:
                    inv = fetch_inventory_for_value("Segment", sel)
                    prods = fetch_products_count_for_value("segment", sel)
                    sc_pct, rem_pct, remaining = compute_scanning_status(inv, prods)
                    fig = px.pie(
                        names=["Scanned", "Remaining"],
                        values=[sc_pct, rem_pct],
                        title=f"Scanned vs Remaining — {sel}",
                        hole=0.3,
                    )
                    st.plotly_chart(fig, key="count_seg_chart")
                    if remaining:
                        st.write(f"**Remaining products in {sel}**")
                        st.dataframe(pd.DataFrame(remaining))
                    else:
                        st.info(f"All products in segment '{sel}' have been scanned.")

            elif dash_type == "Family":
                families = get_unique_values_product_count_collection("family")
                sel = st.selectbox("Select Family", families, key="count_fam_sel")
                if sel:
                    inv = fetch_inventory_for_value("Family", sel)
                    prods = fetch_products_count_for_value("family", sel)
                    sc_pct, rem_pct, remaining = compute_scanning_status(inv, prods)
                    fig = px.pie(
                        names=["Scanned", "Remaining"],
                        values=[sc_pct, rem_pct],
                        title=f"Scanned vs Remaining — {sel}",
                        hole=0.3,
                    )
                    st.plotly_chart(fig, key="count_fam_chart")
                    if remaining:
                        st.write(f"**Remaining products in {sel}**")
                        st.dataframe(pd.DataFrame(remaining))
                    else:
                        st.info(f"All products in family '{sel}' have been scanned.")

        with tab3:
            st.subheader("Near Expiry Dashboard")
            expiry_range = st.selectbox("Select Expiry Range (days)", [15, 20, 30], index=0)
            today = pd.Timestamp.now().normalize()
            expiry_limit = today + pd.Timedelta(days=expiry_range)

            # Fetch all records and filter in Python — MongoDB $lte on DD/MM/YYYY strings
            # gives wrong results because the format is not lexicographically sortable.
            all_products = list(products_collection.find({}, {"_id": 0}))

            def _parse_expiry(prod):
                try:
                    return pd.to_datetime(prod["expiry_date"], format="%d/%m/%Y")
                except Exception:
                    return None

            expiring = [
                p for p in all_products
                if (dt := _parse_expiry(p)) is not None and today <= dt <= expiry_limit
            ]

            total = len(all_products)
            exp_count = len(expiring)
            exp_pct = (exp_count / total * 100) if total > 0 else 0

            fig = px.pie(
                names=["Expiring", "Not Expiring"],
                values=[exp_pct, 100 - exp_pct],
                title=f"Products Expiring Within {expiry_range} Days",
                hole=0.3,
            )
            st.plotly_chart(fig, key="near_expiry_chart")

            if expiring:
                st.write(f"**Products expiring within {expiry_range} days ({exp_count} items)**")
                st.dataframe(pd.DataFrame(expiring))
            else:
                st.info(f"No products are expiring within the next {expiry_range} days.")

        with tab4:
            st.subheader("Scanned Products Raw Data")
            selected_collection = st.radio(
                "Select Collection:",
                ["Expiry Product Database", "Product Count Database"],
                key="raw_data_collection",
            )
            collection = {
                "Expiry Product Database": products_collection,
                "Product Count Database": product_count_collection,
            }[selected_collection]

            filter_option = st.selectbox("Filter By:", ["All Data", "Segment", "Family"])

            if filter_option == "All Data":
                data = list(collection.find({}, {"_id": 0}))
                if data:
                    st.dataframe(pd.DataFrame(data))
                else:
                    st.info("No data available in the selected collection.")

            elif filter_option == "Segment":
                if selected_collection == "Expiry Product Database":
                    segs = get_unique_values_product_collection("segment")
                else:
                    segs = get_unique_values_product_count_collection("segment")
                sel_seg = st.selectbox("Select Segment", segs, key="raw_seg_filter")
                if sel_seg:
                    data = list(collection.find({"segment": sel_seg}, {"_id": 0}))
                    if data:
                        st.dataframe(pd.DataFrame(data))
                    else:
                        st.info(f"No data found for segment '{sel_seg}'.")

            elif filter_option == "Family":
                if selected_collection == "Expiry Product Database":
                    fams = get_unique_values_product_collection("family")
                else:
                    fams = get_unique_values_product_count_collection("family")
                sel_fam = st.selectbox("Select Family", fams, key="raw_fam_filter")
                if sel_fam:
                    data = list(collection.find({"family": sel_fam}, {"_id": 0}))
                    if data:
                        st.dataframe(pd.DataFrame(data))
                    else:
                        st.info(f"No data found for family '{sel_fam}'.")
