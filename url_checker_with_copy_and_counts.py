import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import pandas as pd
import threading

# ---------------------------
# URL Checking Logic
# ---------------------------

def check_url(url):
    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        code = response.status_code

        if code in [301, 302]:
            redirect_url = response.headers.get("Location", "")
            final_url = get_final_url(redirect_url)
            return "Redirect", redirect_url or "", final_url or "", code

        if code == 200:
            return "Working", "", url, code

        return f"Error {code}", "", "", code

    except Exception:
        return "Failed", "", "", ""

def get_final_url(url):
    try:
        if not url:
            return ""
        r = requests.get(url, timeout=10, allow_redirects=True)
        return r.url
    except Exception:
        return url or ""

# ---------------------------
# Load / Export
# ---------------------------

def load_file():
    path = filedialog.askopenfilename(
        filetypes=[("Excel/CSV Files", "*.xlsx *.csv"), ("All files", "*.*")]
    )
    if not path:
        return
    try:
        if path.lower().endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        if "URL" not in df.columns:
            messagebox.showerror("Error", "Your file must contain a column named 'URL'")
            return
        input_box.delete("1.0", tk.END)
        for url in df["URL"].dropna().astype(str).tolist():
            input_box.insert(tk.END, url.strip() + "\n")
        messagebox.showinfo("Loaded", f"Loaded {len(df)} URLs (rows in file).")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def export_results():
    if not results_data:
        messagebox.showerror("Error", "No results to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
    if not path:
        return
    df = pd.DataFrame(results_data)
    try:
        if path.lower().endswith(".csv"):
            df.to_csv(path, index=False)
        else:
            df.to_excel(path, index=False)
        messagebox.showinfo("Saved", f"Saved results to {path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------------------
# Worker
# ---------------------------

results_data = []

def start_check():
    threading.Thread(target=check_links, daemon=True).start()

def check_links():
    global results_data
    results_data = []
    # clear tree
    for it in tree.get_children():
        tree.delete(it)

    raw = input_box.get("1.0", tk.END).strip()
    if not raw:
        messagebox.showerror("Error", "Please paste URLs (one per line).")
        return
    urls = [u.strip() for u in raw.splitlines() if u.strip()]
    total = len(urls)
    progress["maximum"] = total
    progress["value"] = 0
    count_label.config(text=f"Checked: 0/{total}")
    root.update_idletasks()

    working = redirected = broken = 0

    for i, url in enumerate(urls, start=1):
        status, redirect_to, final_url, code = check_url(url)
        results_data.append({
            "Original URL": url,
            "Status": status,
            "Redirect To": redirect_to,
            "Final URL": final_url,
            "HTTP Code": code
        })

        # determine row color tag
        if status == "Working":
            tag = "green"
            working += 1
        elif status == "Redirect":
            tag = "blue"
            redirected += 1
        else:
            tag = "red"
            broken += 1

        tree.insert("", "end", values=(url, status, redirect_to, final_url, code), tags=(tag,))

        # update progress
        progress["value"] = i
        count_label.config(text=f"Checked: {i}/{total}")
        root.update_idletasks()

    # final summary label update
    summary_text = f"Total: {total} | Working: {working} | Redirects: {redirected} | Broken/Failed: {broken}"
    summary_label.config(text=summary_text)

    # show completion popup with final counts
    messagebox.showinfo("Completed", f"URL check completed.\n\n{summary_text}")

# ---------------------------
# Tree selection + Copy helpers
# ---------------------------

def on_tree_double_click(event):
    # open default browser for final url? (optional)
    # keep simple: copy original url to clipboard on double-click
    copy_selected_field("Original URL")

def copy_selected_field(field_name):
    sel = tree.selection()
    if not sel:
        status_bar.set("No row selected to copy.")
        return
    item = sel[0]
    vals = tree.item(item, "values")
    # columns: 0=URL,1=Status,2=Redirect To,3=Final URL,4=Code
    mapping = {
        "Original URL": 0,
        "Status": 1,
        "Redirect To": 2,
        "Final URL": 3,
        "HTTP Code": 4,
        "Row": None
    }
    idx = mapping.get(field_name)
    if idx is None:
        # copy the entire row as tab separated
        text = "\t".join(str(v) for v in vals)
    else:
        text = str(vals[idx]) if idx < len(vals) else ""
    if not text:
        status_bar.set("Selected field is empty.")
        return
    root.clipboard_clear()
    root.clipboard_append(text)
    status_bar.set(f"Copied {field_name} to clipboard.")

def on_copy_shortcut(event):
    # Ctrl+C copies the Original URL of the currently selected row
    copy_selected_field("Original URL")

def show_context_menu(event):
    # select row under pointer
    iid = tree.identify_row(event.y)
    if iid:
        tree.selection_set(iid)
    menu.post(event.x_root, event.y_root)

# ---------------------------
# GUI Setup
# ---------------------------

root = tk.Tk()
root.title("URL Checker — Column View (Copyable Results + Final Count)")
root.geometry("1100x750")

# Top: input and buttons
top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=8, pady=6)

tk.Label(top_frame, text="Paste URLs (one per line):", font=("Segoe UI", 11)).pack(anchor="w")
input_box = tk.Text(top_frame, height=6, width=140, font=("Segoe UI", 10))
input_box.pack(pady=4)

btns = tk.Frame(top_frame)
btns.pack(fill="x", pady=4)
tk.Button(btns, text="Load from Excel/CSV", command=load_file).pack(side="left", padx=4)
tk.Button(btns, text="Check Links", bg="#0b61a4", fg="white", command=start_check).pack(side="left", padx=6)
tk.Button(btns, text="Export Results", bg="#2d7a2d", fg="white", command=export_results).pack(side="left", padx=6)

# Progress
progress = ttk.Progressbar(root, length=900)
progress.pack(pady=6)
count_label = tk.Label(root, text="Checked: 0/0", font=("Segoe UI", 10))
count_label.pack()

# Treeview (table)
columns = ("Original URL", "Status", "Redirect To", "Final URL", "HTTP Code")
tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
tree.pack(padx=8, pady=8, fill="both", expand=True)

for col in columns:
    tree.heading(col, text=col)
    # allow flexible column width
    if col == "Original URL":
        tree.column(col, width=360, anchor="w")
    elif col == "Final URL":
        tree.column(col, width=300, anchor="w")
    elif col == "Redirect To":
        tree.column(col, width=300, anchor="w")
    else:
        tree.column(col, width=120, anchor="center")

# color tags
tree.tag_configure("green", foreground="green")
tree.tag_configure("red", foreground="red")
tree.tag_configure("blue", foreground="blue")

# Bindings: double-click, right-click menu, Ctrl+C
tree.bind("<Double-1>", on_tree_double_click)
root.bind_all("<Control-c>", on_copy_shortcut)

# Context menu for copying different columns
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Copy Original URL", command=lambda: copy_selected_field("Original URL"))
menu.add_command(label="Copy Final URL", command=lambda: copy_selected_field("Final URL"))
menu.add_command(label="Copy Redirect To", command=lambda: copy_selected_field("Redirect To"))
menu.add_command(label="Copy Status", command=lambda: copy_selected_field("Status"))
menu.add_command(label="Copy HTTP Code", command=lambda: copy_selected_field("HTTP Code"))
menu.add_separator()
menu.add_command(label="Copy Entire Row", command=lambda: copy_selected_field("Row"))
tree.bind("<Button-3>", show_context_menu)  # right click

# Summary
summary_label = tk.Label(root, text="Total: 0 | Working: 0 | Redirects: 0 | Broken: 0", font=("Segoe UI", 11, "bold"))
summary_label.pack(pady=6)

# Status bar (one-line messages)
status_frame = tk.Frame(root)
status_frame.pack(fill="x", side="bottom")
status_bar = tk.StringVar()
status_bar.set("Ready")
status_label = tk.Label(status_frame, textvariable=status_bar, anchor="w")
status_label.pack(fill="x", padx=6, pady=4)

# Allow column resizing by user
def enable_column_resize(event):
    for col in columns:
        tree.column(col, stretch=True)
root.bind("<Configure>", enable_column_resize)

root.mainloop()
