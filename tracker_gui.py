import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd


df = pd.DataFrame()  # Initialize empty dataframe

USER_CATEGORY_RULES = {}


# Category keywords
CATEGORY_KEYWORDS = {
    "swiggy": "Food",
    "zomato": "Food",
    "dominos": "Food",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "petrol": "Transport",
    "uber": "Transport",
    "ola": "Transport",
    "electricity": "Utilities",
    "bescom": "Utilities",
    "mobile": "Utilities",
    "recharge": "Utilities",
    "rent": "Housing",
    "atm": "Cash Withdrawal",
    "salary": "Income"
}

def categorize(description):
    description = str(description).lower()
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in description:
            return category
    return "Uncategorized"

def clean_and_process(csv_path):
    try:
        df = pd.read_csv(csv_path, skiprows=20)  # Adjust if header starts earlier/later

        print("Detected columns:", list(df.columns))

        desc_col = "Narration"
        amt_col = "Withdrawal Amt."
        date_col = "Date"

        if not all(col in df.columns for col in [desc_col, amt_col, date_col]):
            raise ValueError(f"Missing expected columns: {desc_col}, {amt_col}, or {date_col}")

        df["Category"] = df[desc_col].apply(categorize)
        df["Amount"] = pd.to_numeric(df[amt_col], errors="coerce")
        df["Date"] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)

        return df[["Date", desc_col, "Amount", "Category"]].dropna()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process CSV: {e}")
        return pd.DataFrame()


def upload_csv():
    global df

    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    df = clean_and_process(file_path)
    if df.empty:
        return

    # Clear previous treeview
    for i in tree.get_children():
        tree.delete(i)

    # Insert new data
    for _, row in df.iterrows():
        tree.insert("", "end", values=[row["Date"].date(), row.iloc[1], row["Amount"], row["Category"]])

    # Update totals
    totals = df.groupby("Category")["Amount"].sum()
    result.set("\n".join(f"{cat}: ₹{amt:,.2f}" for cat, amt in totals.items()))

# GUI setup
root = tk.Tk()
root.title("Expense Tracker GUI")
root.geometry("800x600")

frame = tk.Frame(root)
frame.pack(pady=20)

btn = tk.Button(frame, text="Upload Bank CSV", command=upload_csv)
btn.pack()

cols = ["Date", "Description", "Amount", "Category"]
tree = ttk.Treeview(root, columns=cols, show="headings")
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, width=150)
tree.pack(expand=True, fill=tk.BOTH)


# Category selection
category_var = tk.StringVar()
category_menu = ttk.Combobox(root, textvariable=category_var, state="readonly")
category_menu['values'] = list(set(CATEGORY_KEYWORDS.values())) + ["Subscription", "Health", "Gift", "Other"]
category_menu.set("Select Category")
category_menu.pack(pady=5)

# Button to apply category
def apply_category():
    global df
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Select a row", "Please select a transaction.")
        return

    category = category_var.get()
    if category == "Select Category":
        messagebox.showwarning("Select a category", "Please choose a category.")
        return

    narration = tree.item(selected_item)['values'][1]
    if pd.isna(narration):
        return

    # Extract stable keyword: UPI-X-Y-Z → keyword like "FOODBOOK" or "GOOGLE"
    words = narration.lower().split("-")
    EXCLUDE_KEYWORDS = {"upi", "paytm", "gpay", "google", "india", "digital", "com", "recharge", "ybl", "axis", "ok", "bharatpe"}

# Extract first useful keyword that's not in exclude list
    keyword = next(
        (w for w in words if w.isalpha() and w not in EXCLUDE_KEYWORDS and len(w) > 4),
        None
    )

    if not keyword:
        messagebox.showwarning("Keyword Error", "No valid keyword found for matching.")
        return

    USER_CATEGORY_RULES[keyword] = category

    # Apply to all matching rows
    for i, row in df.iterrows():
        if keyword in str(row["Narration"]).lower():
            df.at[i, "Category"] = category

    # Refresh UI
    for i in tree.get_children():
        tree.delete(i)
    for _, row in df.iterrows():
        tree.insert("", "end", values=[row["Date"].date(), row["Narration"], row["Amount"], row["Category"]])

    messagebox.showinfo("Success", f"Categorized all entries with keyword '{keyword}' → {category}")


apply_btn = tk.Button(root, text="Apply Category to Similar", command=apply_category)
apply_btn.pack(pady=5)


result = tk.StringVar()
result_label = tk.Label(root, textvariable=result, font=("Courier", 12), justify="left")
result_label.pack(pady=10)

root.mainloop()
