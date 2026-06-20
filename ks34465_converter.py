#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KS34465 → HP3458A Analyzer CSV konverter
=========================================
A KS34465 mérőprogram kimeneti CSV fájljait konvertálja
az analyze.py által várt formátumra.

Bemeneti formátum (pontosvessző elválasztó, vesszős tizedes):
  "index";"time";"minutes";"dateTime";"K34465.VoltageDC";"Math.Power"
  0;0,075;...;1778918811,434;10,0196568;0

Kimeneti formátum:
  # HP 3458A NPLC Logger
  # Fs: XX.XX SPS
  # ...
  sample_index,voltage_V
  0,+1.001956456e+01
"""

import os
import sys
import csv
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ─── Konverziós logika ───────────────────────────────────────────────────────

def convert_ks34465(input_path: str, output_path: str,
                    range_v: float, nplc: float, label: str) -> int:
    """
    Konvertálja a KS34465 CSV-t az analyzer formátumra.
    Visszatér: a konvertált minták száma.
    """
    indices = []
    times = []
    voltages = []

    with open(input_path, encoding='utf-8', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        # Oszlopindexek dinamikus meghatározása
        h = [col.strip('"') for col in header]
        try:
            idx_time    = h.index('time')
            idx_voltage = next(i for i, c in enumerate(h)
                               if 'voltage' in c.lower() or 'dc' in c.lower())
            idx_dt      = h.index('dateTime') if 'dateTime' in h else None
        except (ValueError, StopIteration) as e:
            raise ValueError(f"Ismeretlen fejlécoszlop: {e}\nFejléc: {h}") from e

        first_unix = None
        for row in reader:
            if not row or not row[0].strip():
                continue
            t_str = row[idx_time].replace(',', '.')
            v_str = row[idx_voltage].replace(',', '.')
            try:
                t = float(t_str)
                v = float(v_str)
            except ValueError:
                continue
            if idx_dt is not None and first_unix is None:
                try:
                    first_unix = float(row[idx_dt].replace(',', '.'))
                except ValueError:
                    pass
            indices.append(len(times))
            times.append(t)
            voltages.append(v)

    n = len(voltages)
    if n < 2:
        raise ValueError("Kevés érvényes adatsor a fájlban.")

    fs = (n - 1) / (times[-1] - times[0])
    timer_s = 1.0 / fs

    if first_unix is not None:
        start_dt = datetime.fromtimestamp(first_unix, tz=timezone.utc)
        start_str = start_dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
    else:
        start_str = 'ismeretlen'

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(f'# HP 3458A NPLC Logger\n')
        f.write(f'# Start: {start_str}\n')
        f.write(f'# Trig_mode: TIMER\n')
        f.write(f'# NPLC: {nplc}\n')
        f.write(f'# AZERO: 1\n')
        f.write(f'# DEFEAT: OFF\n')
        f.write(f'# Range: {range_v} V\n')
        f.write(f'# Line_freq: 50.0 Hz\n')
        f.write(f'# Timer: {timer_s:.6f} s\n')
        f.write(f'# Fs: {fs:.6f} SPS\n')
        f.write(f'# Forrás: {os.path.basename(input_path)}\n')
        if label:
            f.write(f'# Label: {label}\n')
        f.write('sample_index,voltage_V\n')
        for i, v in enumerate(voltages):
            f.write(f'{i},{v:+.9e}\n')

    return n


# ─── GUI ─────────────────────────────────────────────────────────────────────

class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('KS34465 → HP3458A Analyzer Konverter')
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        pad = {'padx': 8, 'pady': 4}

        # ── Bemeneti fájlok ──────────────────────────────────────────
        frm_in = ttk.LabelFrame(self, text='Bemeneti fájlok (KS34465)')
        frm_in.grid(row=0, column=0, columnspan=3, sticky='ew', **pad)

        self.lst_files = tk.Listbox(frm_in, width=70, height=5,
                                    selectmode=tk.EXTENDED)
        self.lst_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb = ttk.Scrollbar(frm_in, orient=tk.VERTICAL,
                           command=self.lst_files.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lst_files.config(yscrollcommand=sb.set)

        btn_frm = ttk.Frame(frm_in)
        btn_frm.pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frm, text='Hozzáad...', command=self._add_files).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frm, text='Eltávolít', command=self._remove_selected).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frm, text='Töröl mind', command=self._clear_files).pack(fill=tk.X, pady=2)

        # ── Kimeneti mappa ───────────────────────────────────────────
        frm_out = ttk.LabelFrame(self, text='Kimeneti mappa')
        frm_out.grid(row=1, column=0, columnspan=3, sticky='ew', **pad)

        self.var_outdir = tk.StringVar(value='(forrás mellé)')
        ttk.Entry(frm_out, textvariable=self.var_outdir, width=55).pack(
            side=tk.LEFT, padx=4, pady=4)
        ttk.Button(frm_out, text='Tallóz...', command=self._browse_outdir).pack(
            side=tk.LEFT, padx=4)
        ttk.Button(frm_out, text='Forrás mellé', command=self._reset_outdir).pack(
            side=tk.LEFT)

        # ── Metaadat ─────────────────────────────────────────────────
        frm_meta = ttk.LabelFrame(self, text='Mérési metaadat')
        frm_meta.grid(row=2, column=0, columnspan=3, sticky='ew', **pad)

        ttk.Label(frm_meta, text='Tartomány (V):').grid(row=0, column=0, sticky='e', padx=4, pady=3)
        self.var_range = tk.StringVar(value='10')
        ttk.Entry(frm_meta, textvariable=self.var_range, width=10).grid(row=0, column=1, sticky='w')

        ttk.Label(frm_meta, text='NPLC:').grid(row=0, column=2, sticky='e', padx=8)
        self.var_nplc = tk.StringVar(value='1')
        ttk.Entry(frm_meta, textvariable=self.var_nplc, width=8).grid(row=0, column=3, sticky='w')

        ttk.Label(frm_meta, text='Megjegyzés:').grid(row=1, column=0, sticky='e', padx=4, pady=3)
        self.var_label = tk.StringVar(value='')
        ttk.Entry(frm_meta, textvariable=self.var_label, width=40).grid(
            row=1, column=1, columnspan=3, sticky='ew', padx=4)

        # ── Fájlnév előtag ───────────────────────────────────────────
        frm_fn = ttk.LabelFrame(self, text='Kimeneti fájlnév')
        frm_fn.grid(row=3, column=0, columnspan=3, sticky='ew', **pad)

        self.var_prefix = tk.StringVar(value='3458A_DCV')
        self.var_suffix = tk.StringVar(value='_converted')
        ttk.Label(frm_fn, text='Előtag:').grid(row=0, column=0, sticky='e', padx=4, pady=3)
        ttk.Entry(frm_fn, textvariable=self.var_prefix, width=20).grid(row=0, column=1, sticky='w')
        ttk.Label(frm_fn, text='Utótag:').grid(row=0, column=2, sticky='e', padx=8)
        ttk.Entry(frm_fn, textvariable=self.var_suffix, width=20).grid(row=0, column=3, sticky='w')
        ttk.Label(frm_fn, text='→ pl.: 3458A_DCV<eredeti>_converted.csv',
                  foreground='gray').grid(row=1, column=0, columnspan=4, sticky='w', padx=4)

        # ── Státusz ──────────────────────────────────────────────────
        self.var_status = tk.StringVar(value='Kész.')
        ttk.Label(self, textvariable=self.var_status, foreground='navy').grid(
            row=4, column=0, columnspan=2, sticky='w', **pad)

        # ── Gombok ───────────────────────────────────────────────────
        ttk.Button(self, text='Konvertálás', command=self._convert,
                   style='Accent.TButton').grid(row=4, column=2, sticky='e', **pad)

    # ── Fájlkezelés ──────────────────────────────────────────────────────────

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title='KS34465 CSV fájlok kiválasztása',
            filetypes=[('CSV fájlok', '*.csv'), ('Minden fájl', '*.*')])
        for p in paths:
            if p not in self.lst_files.get(0, tk.END):
                self.lst_files.insert(tk.END, p)

    def _remove_selected(self):
        for i in reversed(self.lst_files.curselection()):
            self.lst_files.delete(i)

    def _clear_files(self):
        self.lst_files.delete(0, tk.END)

    def _browse_outdir(self):
        d = filedialog.askdirectory(title='Kimeneti mappa')
        if d:
            self.var_outdir.set(d)

    def _reset_outdir(self):
        self.var_outdir.set('(forrás mellé)')

    # ── Konverzió ────────────────────────────────────────────────────────────

    def _convert(self):
        files = list(self.lst_files.get(0, tk.END))
        if not files:
            messagebox.showwarning('Nincs fájl', 'Először adj hozzá bemeneti fájlokat!')
            return

        try:
            range_v = float(self.var_range.get())
            nplc    = float(self.var_nplc.get())
        except ValueError:
            messagebox.showerror('Hiba', 'A tartomány és az NPLC csak szám lehet!')
            return

        prefix  = self.var_prefix.get().strip()
        suffix  = self.var_suffix.get().strip()
        label   = self.var_label.get().strip()
        use_src = self.var_outdir.get() == '(forrás mellé)'

        ok, errors = 0, []
        for path in files:
            src_dir  = os.path.dirname(path)
            basename = os.path.splitext(os.path.basename(path))[0]
            out_name = f'{prefix}{basename}{suffix}.csv'
            out_dir  = src_dir if use_src else self.var_outdir.get()
            out_path = os.path.join(out_dir, out_name)

            self.var_status.set(f'Feldolgozás: {os.path.basename(path)} …')
            self.update_idletasks()
            try:
                n = convert_ks34465(path, out_path, range_v, nplc, label)
                ok += 1
                self.var_status.set(f'OK: {out_name} ({n} minta)')
            except Exception as e:
                errors.append(f'{os.path.basename(path)}: {e}')

        if errors:
            messagebox.showerror('Konverziós hibák', '\n'.join(errors))
        if ok:
            msg = f'{ok} fájl sikeresen konvertálva.'
            if not errors:
                self.var_status.set(msg)
            messagebox.showinfo('Kész', msg)


# ─── Belépési pont ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = ConverterApp()
    app.mainloop()
