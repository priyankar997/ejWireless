import json
import streamlit as st
from datetime import datetime

# ---------- File Names ----------
SALES_FILE = "sales_records.json"
INVENTORY_FILE = "inventory.json"

STORE_LOCATIONS = [
    "1 E Penn Sq",
    "5600 Germantion Ave",
    "2644 Germantion Ave"
]

# ---------- Helper Functions ----------
def load_json(filename, default):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_sales():
    return load_json(SALES_FILE, [])

def save_sales(sales):
    save_json(SALES_FILE, sales)

def load_inventory():
    return load_json(INVENTORY_FILE, {store: {} for store in STORE_LOCATIONS})

def save_inventory(inventory):
    save_json(INVENTORY_FILE, inventory)

def reduce_inventory(store, product, qty):
    inventory = load_inventory()
    if store not in inventory or product not in inventory[store]:
        st.error(f"Product {product} not found in inventory at {store}.")
        return False
    if inventory[store][product] < qty:
        st.error(f"Not enough stock for {product}. Available: {inventory[store][product]}")
        return False
    inventory[store][product] -= qty
    save_inventory(inventory)
    return True

def calculate_totals(sales):
    return {
        "cost": sum(s["cost"] for s in sales),
        "sold": sum(s["sold"] for s in sales),
        "acc": sum(s["acc"] for s in sales),
        "cash": sum(s["sold"] for s in sales if s["payment_method"] == "Cash"),
        "card": sum(s["sold"] for s in sales if s["payment_method"] == "Card")
    }

def show_totals(title, totals):
    st.write(
        f"**{title}** | Cost: ${totals['cost']:.2f} | Sold: ${totals['sold']:.2f} | "
        f"Acc: ${totals['acc']:.2f} | Cash: ${totals['cash']:.2f} | Card: ${totals['card']:.2f}"
    )

# ---------- Streamlit App ----------
st.set_page_config(page_title="Total Wireless App", layout="wide")

st.title("📱 Total Wireless Sales & Inventory App")

# ---------- Employee Login ----------
employee = st.sidebar.text_input("Employee Name", value="").strip()
if not employee:
    st.sidebar.warning("Enter your name to continue")
    st.stop()

st.sidebar.success(f"Logged in as {employee}")

menu = st.sidebar.radio("Menu", ["Add Sale", "Inventory", "Reports"])

# ---------- Add Sale ----------
if menu == "Add Sale":
    st.header("➕ Add Sale")

    store = st.selectbox("Select Store", STORE_LOCATIONS)
    sale_type = st.radio("Sale Type", ["Phone Sale", "Bill Payment"])

    if sale_type == "Phone Sale":
        product = st.text_input("Product Name")
        qty = st.number_input("Quantity", 1, 100, 1)
    else:
        product = "Bill Payment"
        qty = 1

    cost = st.number_input("Cost Price ($)", 0.0, 10000.0, 0.0)
    sold = st.number_input("Sold Price ($)", 0.0, 10000.0, 0.0)
    payment_method = st.selectbox("Payment Method", ["Cash", "Card"])

    if st.button("💾 Save Sale"):
        if not product.strip():
            st.error("Product name cannot be empty.")
        else:
            if sale_type == "Phone Sale" and not reduce_inventory(store, product.strip(), qty):
                st.stop()

            acc = sold - cost
            sales = load_sales()
            sales.append({
                "employee": employee,
                "store": store,
                "date": datetime.now().strftime("%m/%d/%Y %H:%M"),
                "type": sale_type,
                "product": product.strip(),
                "quantity": qty,
                "cost": cost,
                "sold": sold,
                "acc": acc,
                "payment_method": payment_method
            })
            save_sales(sales)
            st.success("✅ Sale saved successfully!")

# ---------- Inventory ----------
elif menu == "Inventory":
    st.header("📦 Inventory Management")

    store = st.selectbox("Select Store", STORE_LOCATIONS, key="inv_store")
    inventory = load_inventory()

    st.subheader("Current Inventory")
    if inventory.get(store):
        st.table([{"Product": p, "Quantity": q} for p, q in inventory[store].items()])
    else:
        st.info("No inventory found for this store.")

    st.subheader("➕ Add / Update Inventory")
    new_product = st.text_input("Product Name", key="inv_product")
    qty_add = st.number_input("Quantity to Add", 1, 500, 1)

    if st.button("Update Inventory"):
        if new_product.strip():
            current_qty = inventory.get(store, {}).get(new_product.strip(), 0)
            if store not in inventory:
                inventory[store] = {}
            inventory[store][new_product.strip()] = current_qty + qty_add
            save_inventory(inventory)
            st.success(f"✅ {new_product} updated. New quantity: {inventory[store][new_product.strip()]}")
        else:
            st.error("Enter a valid product name")

# ---------- Reports ----------
elif menu == "Reports":
    st.header("📊 Sales Reports")

    sales = load_sales()
    if not sales:
        st.info("No sales data available.")
        st.stop()

    report_type = st.radio("Report Type", ["All Stores", "By Store", "By Employee"])

    if report_type == "All Stores":
        totals = calculate_totals(sales)
        show_totals("ALL STORES", totals)
        st.table(sales)

    elif report_type == "By Store":
        store = st.selectbox("Select Store", STORE_LOCATIONS)
        filtered = [s for s in sales if s["store"] == store]
        totals = calculate_totals(filtered)
        show_totals(store, totals)
        st.table(filtered)

    elif report_type == "By Employee":
        employees = list(set(s["employee"] for s in sales))
        emp = st.selectbox("Select Employee", employees)
        filtered = [s for s in sales if s["employee"] == emp]
        totals = calculate_totals(filtered)
        show_totals(emp, totals)
        st.table(filtered)
