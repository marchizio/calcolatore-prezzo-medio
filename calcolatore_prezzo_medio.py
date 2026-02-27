import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

# ── Palette colori ────────────────────────────────────────────────
BG        = "#f5f2ec"
SURFACE   = "#ffffff"
BORDER    = "#ddd8ce"
ACCENT    = "#2a6e4e"
TEXT      = "#1a1a18"
MUTED     = "#6b6860"
INPUT_BG  = "#faf8f4"
ROW_ODD   = "#faf8f4"
ROW_EVEN  = "#ffffff"
RESULT_BG = "#f0ede6"

SAVE_FILE = os.path.expanduser("~/calcolatore_prezzi.json")


class CalcolatoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calcolatore del Prezzo Medio")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(740, 620)

        # Stato valuta
        self.currency_symbol = tk.StringVar(value="€")
        self.currency_pos    = tk.StringVar(value="before")
        self.decimals        = tk.IntVar(value=2)

        # Dati righe
        self.rows = []

        # Variabili sommario (create prima di _build_table)
        self.sum_price_var = tk.StringVar(value="0")
        self.sum_qty_var   = tk.StringVar(value="0")
        self.sum_total_var = tk.StringVar(value="0")

        # Variabili risultati (create prima di _build_table)
        self.avg_price_var = tk.StringVar(value="—")
        self.total_num_var = tk.StringVar(value="—")
        self.total_amt_var = tk.StringVar(value="—")

        self.saved_calcs = self._load_saved()

        self._build_ui()
        self._center_window(820, 700)

    # ── Layout principale ─────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self, bg=BG, padx=20, pady=20)
        outer.pack(fill="both", expand=True)

        card = tk.Frame(outer, bg=SURFACE, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True)

        self._build_header(card)
        self._build_table(card)
        self._build_actions(card)
        self._build_results(card)

    # ── Header ────────────────────────────────────────────────────
    def _build_header(self, parent):
        row = tk.Frame(parent, bg=SURFACE, pady=20, padx=24)
        row.pack(fill="x")

        tk.Label(row, text="Calcolatore del prezzo medio",
                 font=("Helvetica", 26, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left")

        tk.Button(row, text="⚙  Impostazioni valuta",
                  font=("Helvetica", 13),
                  bg=SURFACE, fg=MUTED,
                  relief="solid", bd=1,
                  activebackground=BORDER,
                  cursor="hand2",
                  command=self._open_settings).pack(side="right", padx=4, ipadx=6, ipady=4)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    # ── Tabella ───────────────────────────────────────────────────
    def _build_table(self, parent):
        self.table_frame = tk.Frame(parent, bg=SURFACE)
        self.table_frame.pack(fill="x", padx=24, pady=(14, 0))

        self.table_frame.grid_columnconfigure(1, weight=3)
        self.table_frame.grid_columnconfigure(3, weight=2)
        self.table_frame.grid_columnconfigure(5, weight=3)

        # Intestazioni
        headers = [("", 4), ("Prezzo", 14), ("", 3), ("Numero", 10), ("", 3), ("Totale", 14), ("", 3)]
        for col, (text, w) in enumerate(headers):
            anchor = "e" if text in ("Prezzo", "Numero", "Totale") else "center"
            tk.Label(self.table_frame, text=text,
                     font=("Helvetica", 12, "bold"),
                     bg=SURFACE, fg=MUTED,
                     width=w, anchor=anchor).grid(row=0, column=col, padx=2, pady=(0, 6))

        tk.Frame(self.table_frame, bg=BORDER, height=1).grid(
            row=1, column=0, columnspan=7, sticky="ew", pady=(0, 4))

        # 4 righe iniziali
        for _ in range(4):
            self._add_row()

        # Riga sommario
        self._build_summary_row()

    def _add_row(self, price="", qty=""):
        idx = len(self.rows)
        bg  = ROW_ODD if idx % 2 == 0 else ROW_EVEN

        price_var = tk.StringVar(value=price)
        qty_var   = tk.StringVar(value=qty)
        total_var = tk.StringVar(value="")

        price_var.trace_add("write", lambda *_: self._recalc())
        qty_var.trace_add("write",   lambda *_: self._recalc())

        grid_row = idx + 2

        num_lbl = tk.Label(self.table_frame,
                           text=f"{idx+1}.",
                           font=("Helvetica", 14, "bold"),
                           bg=bg, fg=MUTED, width=4, anchor="w")
        num_lbl.grid(row=grid_row, column=0, padx=(0, 2), pady=2, sticky="nsew")

        price_entry = tk.Entry(self.table_frame,
                               textvariable=price_var,
                               font=("Helvetica", 15),
                               bg=INPUT_BG, fg=TEXT,
                               relief="solid", bd=1,
                               justify="right",
                               insertbackground=ACCENT)
        price_entry.grid(row=grid_row, column=1, padx=2, pady=5, sticky="ew", ipady=7)
        self._style_entry(price_entry)

        op1 = tk.Label(self.table_frame, text="×",
                       font=("Helvetica", 15), bg=bg, fg=MUTED, width=3)
        op1.grid(row=grid_row, column=2, pady=2)

        qty_entry = tk.Entry(self.table_frame,
                             textvariable=qty_var,
                             font=("Helvetica", 15),
                             bg=INPUT_BG, fg=TEXT,
                             relief="solid", bd=1,
                             justify="right",
                             insertbackground=ACCENT)
        qty_entry.grid(row=grid_row, column=3, padx=2, pady=5, sticky="ew", ipady=7)
        self._style_entry(qty_entry)

        op2 = tk.Label(self.table_frame, text="=",
                       font=("Helvetica", 15), bg=bg, fg=MUTED, width=3)
        op2.grid(row=grid_row, column=4, pady=2)

        total_lbl = tk.Label(self.table_frame,
                             textvariable=total_var,
                             font=("Helvetica", 15),
                             bg=bg, fg=MUTED,
                             anchor="e", width=14)
        total_lbl.grid(row=grid_row, column=5, padx=2, pady=2, sticky="ew")

        del_btn = tk.Button(self.table_frame, text="✕",
                            font=("Helvetica", 11),
                            bg=bg, fg="#e74c3c",
                            relief="flat", bd=0,
                            cursor="hand2",
                            command=lambda i=idx: self._delete_row(i))
        del_btn.grid(row=grid_row, column=6, padx=(4, 0))

        self.rows.append({
            "price_var": price_var,
            "qty_var":   qty_var,
            "total_var": total_var,
            "widgets":   [num_lbl, price_entry, op1, qty_entry, op2, total_lbl, del_btn],
            "grid_row":  grid_row,
        })

        self._recalc()

    def _delete_row(self, idx):
        if len(self.rows) <= 1:
            messagebox.showwarning("Attenzione", "Deve esserci almeno una riga.")
            return
        for w in self.rows[idx]["widgets"]:
            w.destroy()
        self.rows.pop(idx)
        self._rebuild_numbering()
        self._recalc()

    def _rebuild_numbering(self):
        for i, row in enumerate(self.rows):
            bg = ROW_ODD if i % 2 == 0 else ROW_EVEN
            new_grid_row = i + 2
            row["widgets"][0].config(text=f"{i+1}.", bg=bg)
            for w in row["widgets"]:
                if isinstance(w, tk.Label):
                    w.config(bg=bg)
                w.grid(row=new_grid_row)
            row["grid_row"] = new_grid_row
        sum_row = len(self.rows) + 2
        for col, w in enumerate(self.summary_widgets):
            w.grid(row=sum_row, column=col)

    def _build_summary_row(self):
        sum_row = len(self.rows) + 2

        tk.Frame(self.table_frame, bg=BORDER, height=1).grid(
            row=sum_row - 1, column=0, columnspan=7, sticky="ew", pady=(4, 0))

        w0 = tk.Label(self.table_frame, bg=SURFACE, width=4)
        w0.grid(row=sum_row, column=0)

        w1 = tk.Label(self.table_frame, textvariable=self.sum_price_var,
                      font=("Helvetica", 15, "bold"),
                      bg=SURFACE, fg=ACCENT, anchor="e")
        w1.grid(row=sum_row, column=1, padx=2, pady=8, sticky="ew")

        w2 = tk.Label(self.table_frame, text="×",
                      font=("Helvetica", 14), bg=SURFACE, fg=MUTED, width=3)
        w2.grid(row=sum_row, column=2)

        w3 = tk.Label(self.table_frame, textvariable=self.sum_qty_var,
                      font=("Helvetica", 15, "bold"),
                      bg=SURFACE, fg=MUTED, anchor="e")
        w3.grid(row=sum_row, column=3, padx=2, sticky="ew")

        w4 = tk.Label(self.table_frame, text="=",
                      font=("Helvetica", 14), bg=SURFACE, fg=MUTED, width=3)
        w4.grid(row=sum_row, column=4)

        w5 = tk.Label(self.table_frame, textvariable=self.sum_total_var,
                      font=("Helvetica", 15, "bold"),
                      bg=SURFACE, fg=TEXT, anchor="e")
        w5.grid(row=sum_row, column=5, padx=2, sticky="ew")

        w6 = tk.Label(self.table_frame, bg=SURFACE, width=3)
        w6.grid(row=sum_row, column=6)

        self.summary_widgets = [w0, w1, w2, w3, w4, w5, w6]

    # ── Azioni ────────────────────────────────────────────────────
    def _build_actions(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        row = tk.Frame(parent, bg=SURFACE, pady=10, padx=20)
        row.pack(fill="x")

        tk.Button(row, text="+",
                  font=("Helvetica", 18, "bold"),
                  bg=ACCENT, fg="white",
                  width=3, height=1,
                  relief="flat", bd=0,
                  cursor="hand2",
                  activebackground="#1d5a3e",
                  command=self._add_row).pack(side="left", ipadx=4, ipady=2)

        right = tk.Frame(row, bg=SURFACE)
        right.pack(side="right")

        tk.Button(right, text="💾", font=("Helvetica", 17),
                  bg=SURFACE, fg=TEXT, relief="flat", bd=0,
                  cursor="hand2", activebackground=BORDER,
                  command=self._save_calc).pack(side="left", padx=6)

        tk.Button(right, text="↺", font=("Helvetica", 18),
                  bg=SURFACE, fg=TEXT, relief="flat", bd=0,
                  cursor="hand2", activebackground=BORDER,
                  command=self._reset).pack(side="left", padx=6)

        self.saved_var = tk.StringVar(value="Calcoli salvati...")
        self.saved_menu = ttk.Combobox(right, textvariable=self.saved_var,
                                       state="readonly", width=24,
                                       font=("Helvetica", 13))
        self.saved_menu.pack(side="left", padx=(8, 0))
        self.saved_menu.bind("<<ComboboxSelected>>", self._load_selected)
        self._refresh_saved_menu()

    # ── Risultati ─────────────────────────────────────────────────
    def _build_results(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        res = tk.Frame(parent, bg=RESULT_BG, pady=24, padx=28)
        res.pack(fill="x")

        def result_col(label, var, accent=False):
            col = tk.Frame(res, bg=RESULT_BG)
            col.pack(side="left", expand=True, fill="x", padx=10)
            tk.Label(col, text=label.upper(),
                     font=("Helvetica", 10), bg=RESULT_BG, fg=MUTED).pack(anchor="w")
            tk.Label(col, textvariable=var,
                     font=("Helvetica", 26, "bold"),
                     bg=RESULT_BG,
                     fg=ACCENT if accent else TEXT).pack(anchor="w", pady=(4, 0))

        result_col("Prezzo medio",   self.avg_price_var, accent=True)
        result_col("Numero totale",  self.total_num_var)
        result_col("Importo totale", self.total_amt_var)

    # ── Calcolo ───────────────────────────────────────────────────
    def _recalc(self):
        sym = self.currency_symbol.get()
        pos = self.currency_pos.get()
        dec = self.decimals.get()

        def fmt(n):
            s = f"{n:.{dec}f}"
            return f"{sym}{s}" if pos == "before" else f"{s}{sym}"

        total_qty = 0.0
        total_amt = 0.0
        sum_price = 0.0

        for row in self.rows:
            try:
                p = float(row["price_var"].get())
                q = float(row["qty_var"].get())
                row["total_var"].set(fmt(p * q))
                row["widgets"][5].config(fg=TEXT)
                total_qty += q
                total_amt += p * q
                sum_price += p
            except ValueError:
                row["total_var"].set("")

        self.sum_price_var.set(f"{sum_price:.{dec}f}" if sum_price else "0")
        self.sum_qty_var.set(
            str(int(total_qty)) if total_qty == int(total_qty) else f"{total_qty:.{dec}f}"
        )
        self.sum_total_var.set(fmt(total_amt) if total_amt else "0")

        if total_qty > 0:
            avg = total_amt / total_qty
            self.avg_price_var.set(fmt(avg))
            self.total_num_var.set(
                str(int(total_qty)) if total_qty == int(total_qty) else f"{total_qty:.{dec}f}"
            )
            self.total_amt_var.set(fmt(total_amt))
        else:
            self.avg_price_var.set("—")
            self.total_num_var.set("—")
            self.total_amt_var.set("—")

    # ── Impostazioni valuta ───────────────────────────────────────
    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("Impostazioni valuta")
        win.configure(bg=SURFACE)
        win.resizable(False, False)
        win.grab_set()
        self._center_child(win, 340, 290)

        pad = dict(padx=20, pady=6)

        tk.Label(win, text="Simbolo valuta", font=("Helvetica", 13),
                 bg=SURFACE, fg=MUTED, anchor="w").pack(fill="x", **pad)
        tk.Entry(win, textvariable=self.currency_symbol,
                 font=("Helvetica", 15), bg=INPUT_BG,
                 relief="solid", bd=1, justify="center").pack(fill="x", padx=20, pady=(0, 8), ipady=4)

        tk.Label(win, text="Posizione simbolo", font=("Helvetica", 13),
                 bg=SURFACE, fg=MUTED, anchor="w").pack(fill="x", **pad)
        ttk.Combobox(win, textvariable=self.currency_pos,
                     values=["before", "after"], state="readonly",
                     font=("Helvetica", 13)).pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(win, text="Decimali", font=("Helvetica", 13),
                 bg=SURFACE, fg=MUTED, anchor="w").pack(fill="x", **pad)
        ttk.Combobox(win, textvariable=self.decimals,
                     values=[0, 2, 3, 4], state="readonly",
                     font=("Helvetica", 13)).pack(fill="x", padx=20, pady=(0, 14))

        def apply():
            self._recalc()
            win.destroy()

        tk.Button(win, text="Applica", font=("Helvetica", 14, "bold"),
                  bg=ACCENT, fg="white", relief="flat",
                  activebackground="#1d5a3e", cursor="hand2",
                  command=apply).pack(fill="x", padx=20, pady=(0, 16))

    # ── Salva / Carica ────────────────────────────────────────────
    def _save_calc(self):
        name = simpledialog.askstring("Salva calcolo", "Nome del calcolo:", parent=self)
        if not name:
            return
        self.saved_calcs[name] = {
            "rows": [{"price": r["price_var"].get(), "qty": r["qty_var"].get()} for r in self.rows],
            "currency": {
                "symbol":   self.currency_symbol.get(),
                "pos":      self.currency_pos.get(),
                "decimals": self.decimals.get(),
            }
        }
        self._persist_saved()
        self._refresh_saved_menu()
        messagebox.showinfo("Salvato", f'"{name}" salvato con successo.')

    def _load_selected(self, _=None):
        name = self.saved_var.get()
        if name not in self.saved_calcs:
            return
        calc = self.saved_calcs[name]
        c = calc.get("currency", {})
        self.currency_symbol.set(c.get("symbol", "€"))
        self.currency_pos.set(c.get("pos", "before"))
        self.decimals.set(c.get("decimals", 2))
        self._reset(rows_data=calc.get("rows", []))
        self.saved_var.set("Calcoli salvati...")

    def _reset(self, rows_data=None):
        for row in self.rows:
            for w in row["widgets"]:
                w.destroy()
        self.rows.clear()

        data = rows_data or [{} for _ in range(4)]
        for d in data:
            self._add_row(price=d.get("price", ""), qty=d.get("qty", ""))

        sum_row = len(self.rows) + 2
        for col, w in enumerate(self.summary_widgets):
            w.grid(row=sum_row, column=col)

        self._recalc()

    def _refresh_saved_menu(self):
        keys = list(self.saved_calcs.keys())
        self.saved_menu["values"] = keys if keys else []

    def _persist_saved(self):
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self.saved_calcs, f, indent=2)
        except Exception:
            pass

    def _load_saved(self):
        try:
            with open(SAVE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    # ── Utilità ───────────────────────────────────────────────────
    def _style_entry(self, entry):
        entry.bind("<FocusIn>",  lambda e: entry.config(
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=ACCENT))
        entry.bind("<FocusOut>", lambda e: entry.config(
            highlightthickness=1, highlightcolor=BORDER, highlightbackground=BORDER))

    def _center_window(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _center_child(self, win, w, h):
        x = self.winfo_x() + (self.winfo_width()  - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    app = CalcolatoreApp()
    app.mainloop()
