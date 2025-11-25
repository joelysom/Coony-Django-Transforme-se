#!/usr/bin/env python3
"""
DB Viewer (Tkinter)

Usage:
  python db_viewer.py

Place your project's `db.sqlite3` in the same folder (default), or choose another file.
Login: ADMIN / ADMIN

This tool is a local desktop helper to inspect your SQLite DB. It is meant to run
locally by you — it does not transmit data anywhere.
"""
import os
import sqlite3
import csv
import threading
import time
import json
import shutil
from datetime import datetime
import io
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception:
    raise SystemExit('Tkinter is required to run this tool')

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Optional: matplotlib for analytics
try:
    import matplotlib
    matplotlib.use('Agg')  # headless backend
    import matplotlib.pyplot as plt
    MPL_AVAILABLE = True
except Exception:
    MPL_AVAILABLE = False

# Optional: Django password hashing for Usuario.senha updates
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coony.settings')
    django.setup()
    from django.contrib.auth.hashers import make_password, check_password
    HASHING_AVAILABLE = True
except Exception:
    HASHING_AVAILABLE = False


ORANGE = '#f68b4a'
WHITE = '#ffffff'
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'usuarios', 'static', 'img', 'Logo.png')


class DBViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Coony — DB Viewer')
        self.root.geometry('1000x700')
        self.db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
        self.conn = None
        # Pagination / sorting state
        self.page_size = 50
        self.current_page = 0
        self.total_rows = 0
        self.sort_column = None
        self.sort_dir = 'ASC'
        self.active_filters = []  # advanced filters placeholder (list of (col, op, value_tuple))
        self.search_query = ''
        self._fk_cache = {}

        # Styles
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TButton', background=ORANGE, foreground='white')
        style.configure('Header.TLabel', font=('Poppins', 14, 'bold'))

        self._build_login()

    def _build_login(self):
        self.clear_root()
        # Background gradient canvas (fake 3D ambient)
        bg = tk.Canvas(self.root, highlightthickness=0)
        bg.pack(fill='both', expand=True)
        self._login_bg_canvas = bg
        self._draw_login_bg_gradient()

        frame = ttk.Frame(bg, padding=0)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        # Animated card container
        card_shadow = tk.Frame(frame, bg='#d75f18')  # shadow color
        card_shadow.pack()
        card = tk.Frame(card_shadow, bg='#ffffff', bd=0, highlightthickness=1, highlightbackground='#eee')
        card.pack(padx=10, pady=10)
        self._login_card = card
        self._login_card_shadow = card_shadow

        # Provide smooth animation state
        self._card_target_offset = (0, 0)
        self._card_current_offset = (0, 0)
        self._animating_card = False
        card.bind('<Enter>', lambda e: self._start_card_anim())
        card.bind('<Leave>', lambda e: self._reset_card_anim())
        card.bind('<Motion>', self._on_card_motion)

        # Logo
        logo_container = tk.Frame(card, bg='#ffffff')
        logo_container.pack(pady=(10, 6))
        if PIL_AVAILABLE and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img = img.convert('RGBA')
                img.thumbnail((240, 90), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(logo_container, image=self.logo_img, bg='#ffffff').pack()
            except Exception:
                tk.Label(logo_container, text='[logo erro]', fg='red', bg='#ffffff', font=('Poppins', 14, 'bold')).pack()
        else:
            tk.Label(logo_container, text='[logo ausente]', fg='red', bg='#ffffff', font=('Poppins', 14, 'bold')).pack()

        tk.Label(card, text='Acesse seu banco local (SQLite)', font=('Poppins', 11), bg='#ffffff', fg='#333').pack(pady=(0, 15))

        form = tk.Frame(card, bg='#ffffff')
        form.pack()

        tk.Label(form, text='Usuário:', bg='#ffffff').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.user_entry = ttk.Entry(form)
        self.user_entry.grid(row=0, column=1, padx=4, pady=4)

        tk.Label(form, text='Senha:', bg='#ffffff').grid(row=1, column=0, sticky='e', padx=4, pady=4)
        self.pass_entry = ttk.Entry(form, show='*')
        self.pass_entry.grid(row=1, column=1, padx=4, pady=4)

        btn_frame = tk.Frame(card, bg='#ffffff')
        btn_frame.pack(pady=12)

        ttk.Button(btn_frame, text='Escolher DB...', command=self.choose_db).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text='Entrar', command=self._on_login).grid(row=0, column=1, padx=6)

        hint = tk.Label(card, text='Login: ADMIN / ADMIN — arquivo padrão db.sqlite3', fg='#666', bg='#ffffff', wraplength=300, justify='center')
        hint.pack(pady=(4, 12))
        self._animate_bg()

    def _draw_login_bg_gradient(self):
        c = self._login_bg_canvas
        w = c.winfo_width() or self.root.winfo_width()
        h = c.winfo_height() or self.root.winfo_height()
        c.delete('grad')
        # Simple vertical gradient using rectangles
        steps = 40
        for i in range(steps):
            ratio = i / steps
            # interpolate between ORANGE and WHITE
            def interp(a,b): return int(a + (b-a)*ratio)
            r1,g1,b1 = (246,139,74)
            r2,g2,b2 = (255,255,255)
            r = interp(r1,r2); g = interp(g1,g2); b = interp(b1,b2)
            color = f'#{r:02x}{g:02x}{b:02x}'
            c.create_rectangle(0, int(h*(i/steps)), w, int(h*((i+1)/steps)), fill=color, outline=color, tags='grad')
        c.lower('grad')
        c.bind('<Configure>', lambda e: self._draw_login_bg_gradient())

    def _on_card_motion(self, event):
        card = self._login_card
        w = card.winfo_width(); h = card.winfo_height()
        if w == 0 or h == 0: return
        x = event.x; y = event.y
        cx = w/2; cy = h/2
        # Compute tilt offset limited
        max_off = 12
        dx = (x - cx) / cx * max_off
        dy = (y - cy) / cy * max_off
        self._card_target_offset = (dx, dy)
        if not self._animating_card:
            self._start_card_anim()

    def _start_card_anim(self):
        if self._animating_card:
            return
        self._animating_card = True
        self._run_card_anim()

    def _reset_card_anim(self):
        self._card_target_offset = (0,0)
        if not self._animating_card:
            self._start_card_anim()

    def _run_card_anim(self):
        # Smooth approach
        tx, ty = self._card_target_offset
        cx, cy = self._card_current_offset
        nx = cx + (tx - cx) * 0.15
        ny = cy + (ty - cy) * 0.15
        self._card_current_offset = (nx, ny)
        # Apply transform via shadow reposition
        shadow = self._login_card_shadow
        # Place relative using padding
        pad_x = 10 + nx
        pad_y = 10 + ny
        for child in shadow.pack_slaves():
            pass  # no-op; we keep pack
        shadow.configure(padx=int(pad_x), pady=int(pad_y))
        # Simulate perspective by changing highlight color
        card = self._login_card
        tilt_intensity = int(min(255, max(0, 220 + nx*2 - ny*2)))
        edge_color = f'#{tilt_intensity:02x}{tilt_intensity:02x}{tilt_intensity:02x}'
        card.configure(highlightbackground=edge_color)
        if abs(tx - nx) < 0.5 and abs(ty - ny) < 0.5 and tx == 0 and ty == 0:
            self._animating_card = False
            return
        self.root.after(16, self._run_card_anim)

    def _animate_bg(self):
        # Gentle pulsing overlay
        c = self._login_bg_canvas
        t = time.time()
        alpha = (0.5 + 0.5 * ( (t*0.3) % 1))
        # create or update overlay
        c.delete('pulse')
        overlay_color = '#ffffff' if alpha < 0.75 else '#ffe3d0'
        w = c.winfo_width(); h = c.winfo_height()
        c.create_rectangle(0,0,w,h, fill=overlay_color, stipple='gray25', outline='', tags='pulse')
        c.lower('pulse')
        c.after(400, self._animate_bg)

    def choose_db(self):
        path = filedialog.askopenfilename(title='Escolha o arquivo SQLite', filetypes=[('SQLite DB', '*.sqlite3;*.db;*.sqlite'), ('All files', '*.*')])
        if path:
            self.db_path = path
            messagebox.showinfo('DB selecionado', f'Selecionado: {os.path.basename(path)}')

    def _on_login(self):
        user = self.user_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        if user.upper() == 'ADMIN' and pwd.upper() == 'ADMIN':
            # show loading
            self._show_loading_then_main()
        else:
            messagebox.showerror('Autenticação', 'Usuário ou senha incorretos')

    def _show_loading_then_main(self):
        self.clear_root()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill='both')

        ttk.Label(frame, text='Carregando dados...', font=('Poppins', 14)).pack(pady=(10, 10))

        pb = ttk.Progressbar(frame, orient='horizontal', mode='indeterminate', length=320)
        pb.pack(pady=20)
        pb.start(10)

        # small animated dots
        dots = ttk.Label(frame, text='')
        dots.pack()

        def animate_and_open():
            for i in range(30):
                dots['text'] = '.' * (i % 4)
                time.sleep(0.08)
            # try connect
            try:
                # Allow connection to be used across threads (we create it during the background
                # animation thread but use it from the main Tkinter thread). For a small local
                # inspection tool this is acceptable; for heavy concurrent use consider using
                # a dedicated DB thread or open/close connections in the thread that uses them.
                self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            except Exception as e:
                messagebox.showerror('Erro', f'Falha ao abrir DB:\n{e}')
                self._build_login()
                return
            pb.stop()
            self._build_main()

        threading.Thread(target=animate_and_open, daemon=True).start()

    def _build_main(self):
        # main UI: left list of tables, right table content
        self.clear_root()
        self.root.title('Coony — DB Viewer — ' + os.path.basename(self.db_path))

        top = ttk.Frame(self.root)
        top.pack(fill='x')
        # Logo small
        if PIL_AVAILABLE and os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((160, 60), Image.LANCZOS)
                self.small_logo = ImageTk.PhotoImage(img)
                ttk.Label(top, image=self.small_logo).pack(side='left', padx=8, pady=8)
            except Exception:
                ttk.Label(top, text='(logo erro)', foreground='red').pack(side='left', padx=8, pady=8)
        else:
            ttk.Label(top, text='(logo ausente)', foreground='red').pack(side='left', padx=8, pady=8)

        ttk.Button(top, text='Escolher outro DB', command=self.choose_db).pack(side='right', padx=8)
        ttk.Button(top, text='Exportar tabela', command=self.export_current_table).pack(side='right')
        ttk.Button(top, text='Backup', command=self.backup_db).pack(side='right')
        ttk.Button(top, text='Restaurar', command=self.restore_db).pack(side='right')
        ttk.Button(top, text='Undo', command=self._undo_last_change).pack(side='right')
        ttk.Button(top, text='Analytics', command=self._open_analytics_dialog).pack(side='right')

        # CRUD buttons (appear after table selection)
        self.crud_frame = ttk.Frame(top)
        self.crud_frame.pack(side='right', padx=12)
        self.btn_add = ttk.Button(self.crud_frame, text='Novo Registro', command=self.add_row, state='disabled')
        self.btn_add.pack(side='left', padx=4)
        self.btn_edit = ttk.Button(self.crud_frame, text='Editar Selecionado', command=self.edit_selected, state='disabled')
        self.btn_edit.pack(side='left', padx=4)
        self.btn_del = ttk.Button(self.crud_frame, text='Excluir Selecionado', command=self.delete_selected, state='disabled')
        self.btn_del.pack(side='left', padx=4)

        container = ttk.Frame(self.root)
        container.pack(expand=True, fill='both')

        left = ttk.Frame(container, width=260)
        left.pack(side='left', fill='y')

        ttk.Label(left, text='Tabelas', font=('Poppins', 12, 'bold')).pack(anchor='w', padx=8, pady=(8, 4))
        self.tables_list = tk.Listbox(left, activestyle='dotbox')
        self.tables_list.pack(expand=True, fill='both', padx=8, pady=4)
        self.tables_list.bind('<<ListboxSelect>>', lambda e: self.on_table_select())

        # Right side: treeview for rows
        right = ttk.Frame(container)
        right.pack(side='left', expand=True, fill='both')

        search_frame = ttk.Frame(right)
        search_frame.pack(fill='x', padx=8, pady=6)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=(0,6))
        ttk.Button(search_frame, text='Pesquisar', command=self.search_rows).pack(side='left')
        ttk.Button(search_frame, text='Filtros...', command=self._open_filters_dialog).pack(side='left', padx=(6,0))

        # Pagination controls
        pag_frame = ttk.Frame(right)
        pag_frame.pack(fill='x', padx=8, pady=(0,6))
        self.btn_prev = ttk.Button(pag_frame, text='◀ Anterior', command=self._prev_page, state='disabled')
        self.btn_prev.pack(side='left')
        self.page_label = ttk.Label(pag_frame, text='Página 1')
        self.page_label.pack(side='left', padx=12)
        self.btn_next = ttk.Button(pag_frame, text='Próxima ▶', command=self._next_page, state='disabled')
        self.btn_next.pack(side='left')
        ttk.Label(pag_frame, text=f'Tamanho página: {self.page_size}').pack(side='right')

        self.tree = ttk.Treeview(right, show='headings')
        self.tree.pack(expand=True, fill='both', padx=8, pady=(0,8))

        # load table list
        self._load_tables()
        self._ensure_audit_table()

    def _load_tables(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
            rows = cur.fetchall()
            self.tables = [r[0] for r in rows]
            self.tables_list.delete(0, tk.END)
            for t in self.tables:
                self.tables_list.insert(tk.END, t)
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao listar tabelas:\n{e}')

    def on_table_select(self):
        sel = self.tables_list.curselection()
        if not sel:
            return
        table = self.tables_list.get(sel[0])
        self.current_table = table
        self._show_table(table)
        # Enable CRUD buttons
        self.btn_add['state'] = 'normal'
        self.btn_edit['state'] = 'normal'
        self.btn_del['state'] = 'normal'
        # Bind double-click edit
        self.tree.bind('<Double-1>', lambda e: self.edit_selected())

    def _show_table(self, table):
        # Reset page when changing table
        self.current_page = 0
        self.sort_column = None
        self.sort_dir = 'ASC'
        self.search_query = ''
        self._refresh_table()

    def _compose_where(self):
        clauses = []
        params = []
        # Advanced filters (future expansion). Each item: (col, op, values) where values is tuple/list
        for col, op, vals in self.active_filters:
            if op.upper() in ('=', '>', '>=', '<', '<='):
                clauses.append(f'"{col}" {op} ?')
                params.append(vals[0])
            elif op.upper() == 'LIKE':
                clauses.append(f'"{col}" LIKE ?')
                params.append(vals[0])
            elif op.upper() == 'IN':
                ph = ','.join(['?']*len(vals))
                clauses.append(f'"{col}" IN ({ph})')
                params.extend(vals)
            elif op.upper() == 'BETWEEN':
                clauses.append(f'"{col}" BETWEEN ? AND ?')
                params.extend(vals[:2])
        # Search query naive concatenation
        if self.search_query and hasattr(self, 'current_table'):
            cur = self.conn.cursor()
            cur.execute(f'PRAGMA table_info("{self.current_table}")')
            cols = [c[1] for c in cur.fetchall()]
            concat = " || '|' || ".join([f'IFNULL(CAST({c} AS TEXT), "")' for c in cols])
            clauses.append(f'({concat}) LIKE ?')
            params.append(f'%{self.search_query}%')
        where = ''
        if clauses:
            where = 'WHERE ' + ' AND '.join(clauses)
        return where, params

    def _refresh_table(self):
        if not hasattr(self, 'current_table'):
            return
        table = self.current_table
        try:
            cur = self.conn.cursor()
            # get columns
            cur.execute(f'PRAGMA table_info("{table}")')
            cols_info = cur.fetchall()
            cols = [c[1] for c in cols_info]
            where, params = self._compose_where()
            # total rows count
            cur.execute(f'SELECT COUNT(*) FROM "{table}" {where}', params)
            self.total_rows = cur.fetchone()[0]
            # paging
            offset = self.current_page * self.page_size
            # adjust current page if overflow
            if offset >= self.total_rows and self.total_rows != 0:
                self.current_page = max((self.total_rows - 1)//self.page_size, 0)
                offset = self.current_page * self.page_size
            order_clause = ''
            if self.sort_column:
                order_clause = f'ORDER BY "{self.sort_column}" {self.sort_dir}'
            sql = f'SELECT * FROM "{table}" {where} {order_clause} LIMIT {self.page_size} OFFSET {offset}'
            cur.execute(sql, params)
            rows = cur.fetchall()
            # reset tree
            self.tree.delete(*self.tree.get_children())
            self.tree['columns'] = cols
            for c in cols:
                # Provide clickable sort
                def _make_sort_callback(colname):
                    return lambda: self._toggle_sort(colname)
                heading_text = c
                if self.sort_column == c:
                    heading_text = f'{c} ({"↑" if self.sort_dir=="ASC" else "↓"})'
                self.tree.heading(c, text=heading_text, command=_make_sort_callback(c))
                self.tree.column(c, width=120, anchor='w')
            for r in rows:
                self.tree.insert('', 'end', values=[str(x) for x in r])
            # update pagination controls
            total_pages = (self.total_rows + self.page_size - 1)//self.page_size if self.total_rows else 1
            self.page_label['text'] = f'Página {self.current_page+1} / {total_pages}  (Total: {self.total_rows})'
            self.btn_prev['state'] = 'normal' if self.current_page > 0 else 'disabled'
            self.btn_next['state'] = 'normal' if (self.current_page+1) < total_pages else 'disabled'
        except Exception as e:
            messagebox.showerror('Erro', f'Erro ao abrir tabela {table}:\n{e}')

    def _toggle_sort(self, col):
        if self.sort_column == col:
            self.sort_dir = 'DESC' if self.sort_dir == 'ASC' else 'ASC'
        else:
            self.sort_column = col
            self.sort_dir = 'ASC'
        self._refresh_table()

    def _next_page(self):
        self.current_page += 1
        self._refresh_table()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table()

    # -------------------- CRUD OPERATIONS --------------------
    def _get_columns(self, table):
        cur = self.conn.cursor()
        cur.execute(f'PRAGMA table_info("{table}")')
        return [c[1] for c in cur.fetchall()]

    def _get_column_defs(self, table):
        cur = self.conn.cursor()
        cur.execute(f'PRAGMA table_info("{table}")')
        info = cur.fetchall()  # cid, name, type, notnull, dflt, pk
        # FK list
        cur.execute(f'PRAGMA foreign_key_list("{table}")')
        fk_rows = cur.fetchall()  # id, seq, table, from, to, on_update, on_delete, match
        fk_map = {r[3]: r[2] for r in fk_rows}  # from_col -> ref_table
        defs = []
        for cid, name, ctype, notnull, dflt, pk in info:
            defs.append({
                'name': name,
                'type': ctype.upper() if ctype else '',
                'pk': pk == 1,
                'fk_table': fk_map.get(name)
            })
        return defs

    def _get_fk_values(self, table):
        if table in self._fk_cache:
            return self._fk_cache[table]
        try:
            cur = self.conn.cursor()
            cur.execute(f'PRAGMA table_info("{table}")')
            cols = [c[1] for c in cur.fetchall()]
            pk = cols[0] if cols else None
            display = None
            # choose a display column heuristically
            for cand in ['nome', 'name', 'titulo', 'title', 'email']:
                if cand in cols:
                    display = cand
                    break
            if not display and len(cols) > 1:
                display = cols[1]
            cur.execute(f'SELECT * FROM "{table}" LIMIT 200')
            rows = cur.fetchall()
            values = []
            for r in rows:
                if pk:
                    pk_val = r[0]
                    if display:
                        # find index of display
                        idx = cols.index(display)
                        values.append(f'{pk_val} — {r[idx]}')
                    else:
                        values.append(str(pk_val))
            self._fk_cache[table] = values
            return values
        except Exception:
            return []

    def add_row(self):
        if not hasattr(self, 'current_table'):
            return
        table = self.current_table
        cols = self._get_columns(table)
        self._open_edit_dialog(table, cols, None)

    def edit_selected(self):
        if not hasattr(self, 'current_table'):
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Editar', 'Selecione uma linha na tabela')
            return
        values = self.tree.item(sel[0], 'values')
        table = self.current_table
        cols = self._get_columns(table)
        self._open_edit_dialog(table, cols, values)

    def delete_selected(self):
        if not hasattr(self, 'current_table'):
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Excluir', 'Selecione uma linha para excluir')
            return
        if messagebox.askyesno('Confirmar exclusão', 'Tem certeza que deseja excluir este registro?'):
            values = self.tree.item(sel[0], 'values')
            table = self.current_table
            cols = self._get_columns(table)
            pk_col = cols[0]  # assume first column is primary key
            pk_val = values[0]
            try:
                # capture BEFORE row
                before_dict = {col: values[i] for i, col in enumerate(cols)}
                cur = self.conn.cursor()
                cur.execute(f'DELETE FROM "{table}" WHERE "{pk_col}" = ?', (pk_val,))
                self.conn.commit()
                self._show_table(table)
                self._refresh_table()
                self._log_change('DELETE', table, pk_val, before_dict, None)
            except Exception as e:
                messagebox.showerror('Excluir', f'Erro ao excluir: {e}')

    def _open_edit_dialog(self, table, cols, values):
        is_edit = values is not None
        win = tk.Toplevel(self.root)
        win.title(('Editar' if is_edit else 'Novo') + f' — {table}')
        win.transient(self.root)
        win.grab_set()

        form = ttk.Frame(win, padding=12)
        form.pack(fill='both', expand=True)

        entries = {}
        # Build column definitions richer
        col_defs = self._get_column_defs(table)
        name_index_map = {d['name']: idx for idx, d in enumerate(col_defs)}
        for i, col in enumerate(cols):
            ttk.Label(form, text=col + ':').grid(row=i, column=0, sticky='e', padx=4, pady=4)
            # Primary key: show but disable edit on update
            state = 'normal'
            show_val = ''
            if is_edit:
                show_val = values[i]
                if i == 0:  # PK
                    state = 'disabled'
            # Special handling for senha field
            if col.lower() == 'senha':
                frame_pwd = ttk.Frame(form)
                frame_pwd.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                hashed_label = ttk.Label(frame_pwd, text='(hash atual – irreversível)', foreground='#888')
                hashed_label.pack(anchor='w')
                current_hash = ttk.Entry(frame_pwd, width=60)
                current_hash.insert(0, show_val)
                current_hash['state'] = 'disabled'
                current_hash.pack(anchor='w', pady=(0,4))

                new_pwd = ttk.Entry(frame_pwd, show='*', width=30)
                new_pwd.pack(anchor='w')
                ttk.Label(frame_pwd, text='Nova senha (deixe vazio p/ manter)', foreground='#666').pack(anchor='w')

                test_frame = ttk.Frame(frame_pwd)
                test_frame.pack(anchor='w', pady=(6,0))
                ttk.Label(test_frame, text='Testar senha:', foreground='#666').pack(side='left')
                test_entry = ttk.Entry(test_frame, show='*', width=24)
                test_entry.pack(side='left', padx=(6,6))

                def testar_senha():
                    cand = test_entry.get().strip()
                    if not cand:
                        messagebox.showinfo('Testar senha', 'Digite uma senha para testar.')
                        return
                    if not show_val:
                        messagebox.showwarning('Testar senha', 'Hash vazio, nada para validar.')
                        return
                    if HASHING_AVAILABLE and check_password(cand, show_val):
                        messagebox.showinfo('Testar senha', 'Senha CORRETA para este hash.')
                    else:
                        messagebox.showerror('Testar senha', 'Senha incorreta.')
                ttk.Button(test_frame, text='Verificar', command=testar_senha).pack(side='left')

                entries[col] = ('password', new_pwd, current_hash)
            else:
                meta_def = col_defs[name_index_map[col]] if col in name_index_map else {'type':'','pk':False,'fk_table':None}
                ctype = meta_def['type']
                fk_table = meta_def['fk_table']
                # Foreign key -> Combobox
                if fk_table:
                    combo_values = self._get_fk_values(fk_table)
                    var = tk.StringVar()
                    cb = ttk.Combobox(form, textvariable=var, values=combo_values, state='readonly', width=50)
                    if show_val:
                        # attempt to preselect by pk prefix
                        for opt in combo_values:
                            if opt.split(' — ')[0] == str(show_val):
                                var.set(opt)
                                break
                    cb.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                    entries[col] = ('combobox', var, fk_table)
                # Boolean
                elif 'BOOL' in ctype or col.lower().startswith('is_'):
                    var = tk.IntVar(value=1 if str(show_val) in ('1','True','true') else 0)
                    chk = ttk.Checkbutton(form, variable=var)
                    chk.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                    entries[col] = ('checkbox', var)
                # Date
                elif 'DATE' in ctype or col.lower().endswith('_date') or col.lower().endswith('_data'):
                    ent = ttk.Entry(form, width=50, state=state)
                    placeholder = show_val if show_val else 'YYYY-MM-DD'
                    ent.insert(0, placeholder)
                    ent.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                    entries[col] = ('date', ent)
                # Integer
                elif 'INT' in ctype and not meta_def['pk']:
                    vcmd = (form.register(lambda s: s.isdigit() or s==''), '%P')
                    ent = ttk.Entry(form, width=50, state=state, validate='key', validatecommand=vcmd)
                    ent.insert(0, show_val)
                    ent.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                    entries[col] = ('int', ent)
                else:
                    ent = ttk.Entry(form, width=50, state=state)
                    ent.grid(row=i, column=1, sticky='w', padx=4, pady=4)
                    ent.insert(0, show_val)
                    entries[col] = ('text', ent)

        btn_bar = ttk.Frame(win)
        btn_bar.pack(pady=10)
        def salvar():
            try:
                cur = self.conn.cursor()
                if is_edit:
                    pk_col = cols[0]
                    pk_val = values[0]
                    # BEFORE row snapshot
                    before_dict = {col: values[i] for i, col in enumerate(cols)}
                    sets = []
                    params = []
                    for col in cols[1:]:  # skip pk
                        meta = entries[col]
                        if meta[0] == 'password':
                            new_pwd_entry = meta[1]
                            raw_pwd = new_pwd_entry.get().strip()
                            if raw_pwd:
                                if HASHING_AVAILABLE:
                                    hashed = make_password(raw_pwd)
                                else:
                                    # Fallback: store raw (NOT recommended)
                                    hashed = raw_pwd
                                sets.append(f'"{col}" = ?')
                                params.append(hashed)
                        elif meta[0] in ('text','date','int'):
                            val = meta[1].get()
                            sets.append(f'"{col}" = ?')
                            params.append(val)
                        elif meta[0] == 'checkbox':
                            val = str(meta[1].get())
                            sets.append(f'"{col}" = ?')
                            params.append(val)
                        elif meta[0] == 'combobox':
                            val = meta[1].get().split(' — ')[0] if meta[1].get() else ''
                            sets.append(f'"{col}" = ?')
                            params.append(val)
                    if sets:
                        params.append(pk_val)
                        sql = f'UPDATE "{table}" SET {", ".join(sets)} WHERE "{pk_col}" = ?'
                        cur.execute(sql, params)
                        self.conn.commit()
                        # AFTER snapshot
                        cur.execute(f'SELECT * FROM "{table}" WHERE "{pk_col}" = ?', (pk_val,))
                        after_row = cur.fetchone()
                        after_dict = {cols[i]: after_row[i] for i in range(len(cols))} if after_row else None
                        self._log_change('UPDATE', table, pk_val, before_dict, after_dict)
                else:
                    cols_insert = []
                    placeholders = []
                    params = []
                    for col in cols:
                        meta = entries[col]
                        if meta[0] == 'password':
                            raw_pwd = meta[1].get().strip()
                            if not raw_pwd:
                                continue  # skip empty password
                            if HASHING_AVAILABLE:
                                hashed = make_password(raw_pwd)
                            else:
                                hashed = raw_pwd
                            cols_insert.append(col)
                            placeholders.append('?')
                            params.append(hashed)
                        elif meta[0] in ('text','date','int'):
                            val = meta[1].get().strip()
                            if val == '' and col == cols[0]:
                                continue
                            cols_insert.append(col)
                            placeholders.append('?')
                            params.append(val)
                        elif meta[0] == 'checkbox':
                            val = str(meta[1].get())
                            cols_insert.append(col)
                            placeholders.append('?')
                            params.append(val)
                        elif meta[0] == 'combobox':
                            val = meta[1].get().split(' — ')[0] if meta[1].get() else ''
                            if val == '' and col == cols[0]:
                                continue
                            cols_insert.append(col)
                            placeholders.append('?')
                            params.append(val)
                    if cols_insert:
                        sql = f'INSERT INTO "{table}" ({', '.join([f'"{c}"' for c in cols_insert])}) VALUES ({', '.join(placeholders)})'
                        cur.execute(sql, params)
                        self.conn.commit()
                        # Determine PK value
                        pk_col = cols[0]
                        pk_val = None
                        if pk_col in cols_insert:
                            # Provided manually
                            pk_val_idx = cols_insert.index(pk_col)
                            pk_val = params[pk_val_idx]
                        else:
                            # fetch last inserted row id (assumes pk is autoincrement first col)
                            cur.execute('SELECT last_insert_rowid()')
                            pk_val = cur.fetchone()[0]
                        cur.execute(f'SELECT * FROM "{table}" WHERE "{pk_col}" = ?', (pk_val,))
                        after_row = cur.fetchone()
                        after_dict = {cols[i]: after_row[i] for i in range(len(cols))} if after_row else None
                        self._log_change('INSERT', table, pk_val, None, after_dict)
                self._show_table(table)
                self._refresh_table()
                win.destroy()
            except Exception as e:
                messagebox.showerror('Salvar', f'Erro ao salvar: {e}')
        ttk.Button(btn_bar, text='Salvar', command=salvar).pack(side='left', padx=6)
        ttk.Button(btn_bar, text='Cancelar', command=win.destroy).pack(side='left', padx=6)

        info = ttk.Label(win, text='Senha é armazenada com hash (não pode ser “descriptografada”). Você pode definir uma nova.', foreground='#555')
        if any(c.lower() == 'senha' for c in cols):
            info.pack(pady=(0,10))

    def search_rows(self):
        q = self.search_var.get().strip()
        if not hasattr(self, 'current_table'):
            messagebox.showinfo('Pesquisar', 'Selecione uma tabela antes de pesquisar')
            return
        self.search_query = q
        self.current_page = 0
        self._refresh_table()

    def export_current_table(self):
        if not hasattr(self, 'current_table'):
            messagebox.showinfo('Exportar', 'Selecione uma tabela primeiro')
            return
        table = self.current_table
        fname = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')], initialfile=f'{table}.csv')
        if not fname:
            return
        try:
            cur = self.conn.cursor()
            cur.execute(f'PRAGMA table_info("{table}")')
            cols = [c[1] for c in cur.fetchall()]
            cur.execute(f'SELECT * FROM "{table}"')
            rows = cur.fetchall()
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                writer.writerows(rows)
            messagebox.showinfo('Exportar', f'Exportado para {fname}')
        except Exception as e:
            messagebox.showerror('Exportar', f'Falha ao exportar: {e}')

    def clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()

    # -------------------- Advanced Filtering --------------------
    def _open_filters_dialog(self):
        if not hasattr(self, 'current_table'):
            messagebox.showinfo('Filtros', 'Selecione uma tabela primeiro')
            return
        win = tk.Toplevel(self.root)
        win.title('Filtros — ' + self.current_table)
        win.transient(self.root)
        win.grab_set()
        frm = ttk.Frame(win, padding=10)
        frm.pack(fill='both', expand=True)
        cols = self._get_columns(self.current_table)
        ops = ['=', 'LIKE', '>', '<', '>=', '<=', 'BETWEEN', 'IN']
        condition_rows = []

        def add_row(pref=None):
            row_frame = ttk.Frame(frm)
            row_frame.pack(fill='x', pady=4)
            col_var = tk.StringVar(value=pref[0] if pref else cols[0])
            op_var = tk.StringVar(value=pref[1] if pref else '=')
            val1_var = tk.StringVar(value=pref[2][0] if pref else '')
            val2_var = tk.StringVar(value=(pref[2][1] if pref and len(pref[2])>1 else ''))
            ttk.Combobox(row_frame, values=cols, textvariable=col_var, width=18, state='readonly').pack(side='left')
            ttk.Combobox(row_frame, values=ops, textvariable=op_var, width=10, state='readonly').pack(side='left', padx=6)
            e1 = ttk.Entry(row_frame, textvariable=val1_var, width=20)
            e1.pack(side='left')
            e2 = ttk.Entry(row_frame, textvariable=val2_var, width=20)
            e2.pack(side='left', padx=6)
            def update_op_display(*_):
                if op_var.get() == 'BETWEEN':
                    e2.configure(state='normal')
                else:
                    if op_var.get() == 'IN':
                        e2.configure(state='disabled')
                    else:
                        e2.configure(state='disabled')
            op_var.trace_add('write', update_op_display)
            update_op_display()
            def remove_row():
                condition_rows.remove(row_frame)
                row_frame.destroy()
            ttk.Button(row_frame, text='Remover', command=remove_row).pack(side='left', padx=6)
            condition_rows.append(row_frame)
            row_frame.meta = (col_var, op_var, val1_var, val2_var)

        # preload existing
        for cond in self.active_filters:
            add_row(pref=(cond[0], cond[1], cond[2]))
        ttk.Button(frm, text='Adicionar condição', command=lambda: add_row()).pack(pady=6)
        def aplicar():
            new_filters = []
            for rf in condition_rows:
                col_v, op_v, v1, v2 = rf.meta
                col = col_v.get(); op = op_v.get(); val1 = v1.get().strip(); val2 = v2.get().strip()
                if not col or not op:
                    continue
                if op == 'BETWEEN':
                    if val1 and val2:
                        new_filters.append((col, op, (val1, val2)))
                elif op == 'IN':
                    if val1:
                        parts = [p.strip() for p in val1.split(',') if p.strip()]
                        if parts:
                            new_filters.append((col, op, tuple(parts)))
                else:
                    if val1:
                        new_filters.append((col, op, (val1,)))
            self.active_filters = new_filters
            self.current_page = 0
            self._refresh_table()
            win.destroy()
        ttk.Button(frm, text='Aplicar', command=aplicar).pack(pady=8)
        ttk.Button(frm, text='Limpar tudo', command=lambda: (setattr(self, 'active_filters', []), setattr(self, 'current_page', 0), self._refresh_table(), win.destroy())).pack(pady=2)

    # -------------------- Audit & Undo --------------------
    def _ensure_audit_table(self):
        try:
            cur = self.conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS _audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                table_name TEXT,
                op TEXT,
                pk TEXT,
                before_json TEXT,
                after_json TEXT
            )''')
            self.conn.commit()
        except Exception:
            pass

    def _log_change(self, op, table, pk, before_dict, after_dict):
        try:
            cur = self.conn.cursor()
            cur.execute('INSERT INTO _audit_log (ts, table_name, op, pk, before_json, after_json) VALUES (?,?,?,?,?,?)', (
                datetime.utcnow().isoformat(), table, op, str(pk),
                json.dumps(before_dict) if before_dict else None,
                json.dumps(after_dict) if after_dict else None
            ))
            self.conn.commit()
        except Exception:
            pass

    def _undo_last_change(self):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT id, op, table_name, pk, before_json, after_json FROM _audit_log ORDER BY id DESC LIMIT 1')
            row = cur.fetchone()
            if not row:
                messagebox.showinfo('Undo', 'Nenhuma mudança para desfazer.')
                return
            log_id, op, table, pk, before_js, after_js = row
            cols = self._get_columns(table)
            if op == 'INSERT':
                cur.execute(f'DELETE FROM "{table}" WHERE "{cols[0]}" = ?', (pk,))
            elif op == 'UPDATE':
                if before_js:
                    before = json.loads(before_js)
                    sets = []
                    params = []
                    for c in cols[1:]:
                        if c in before:
                            sets.append(f'"{c}" = ?')
                            params.append(before[c])
                    params.append(pk)
                    if sets:
                        cur.execute(f'UPDATE "{table}" SET {", ".join(sets)} WHERE "{cols[0]}" = ?', params)
            elif op == 'DELETE':
                if before_js:
                    before = json.loads(before_js)
                    insert_cols = []
                    placeholders = []
                    params = []
                    for c in cols:
                        if c in before:
                            insert_cols.append(f'"{c}"')
                            placeholders.append('?')
                            params.append(before[c])
                    if insert_cols:
                        cur.execute(f'INSERT INTO "{table}" ({", ".join(insert_cols)}) VALUES ({", ".join(placeholders)})', params)
            self.conn.commit()
            # Remove audit entry used for undo
            cur.execute('DELETE FROM _audit_log WHERE id = ?', (log_id,))
            self.conn.commit()
            if hasattr(self, 'current_table') and self.current_table == table:
                self._refresh_table()
            messagebox.showinfo('Undo', f'Desfeito: {op} em {table}.')
        except Exception as e:
            messagebox.showerror('Undo', f'Falha ao desfazer: {e}')

    # -------------------- Backup & Restore --------------------
    def backup_db(self):
        try:
            if self.conn:
                self.conn.commit()
            backups_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            os.makedirs(backups_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d-%H%M%S')
            dest = os.path.join(backups_dir, f'backup-{ts}.sqlite3')
            shutil.copy2(self.db_path, dest)
            messagebox.showinfo('Backup', f'Backup criado: {dest}')
        except Exception as e:
            messagebox.showerror('Backup', f'Falha no backup: {e}')

    def restore_db(self):
        path = filedialog.askopenfilename(title='Selecionar arquivo para restaurar', filetypes=[('SQLite DB','*.sqlite3;*.db;*.sqlite')])
        if not path:
            return
        if not messagebox.askyesno('Restaurar', 'Substituir o banco atual por este arquivo?'):
            return
        try:
            if self.conn:
                self.conn.close()
            shutil.copy2(path, self.db_path)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._load_tables()
            self.current_table = None
            messagebox.showinfo('Restaurar', 'Restauro concluído.')
        except Exception as e:
            messagebox.showerror('Restaurar', f'Falha ao restaurar: {e}')

    # -------------------- Analytics --------------------
    def _open_analytics_dialog(self):
        win = tk.Toplevel(self.root)
        win.title('Analytics')
        win.transient(self.root)
        win.grab_set()
        frm = ttk.Frame(win, padding=10)
        frm.pack(fill='both', expand=True)
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != '_audit_log'")
            tables = [r[0] for r in cur.fetchall()]
            data = []
            for t in tables:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                cnt = cur.fetchone()[0]
                data.append((t, cnt))
            # Display textual
            for t, c in data:
                ttk.Label(frm, text=f'{t}: {c} registros').pack(anchor='w')
            if MPL_AVAILABLE and PIL_AVAILABLE and data:
                names = [d[0] for d in data]
                counts = [d[1] for d in data]
                fig, ax = plt.subplots(figsize=(6,3))
                ax.bar(names, counts, color='#f68b4a')
                ax.set_ylabel('Registros')
                ax.set_xticklabels(names, rotation=45, ha='right')
                fig.tight_layout()
                bio = io.BytesIO()
                fig.savefig(bio, format='png')
                plt.close(fig)
                bio.seek(0)
                img = Image.open(bio)
                img_tk = ImageTk.PhotoImage(img)
                lbl = ttk.Label(frm, image=img_tk)
                lbl.image = img_tk
                lbl.pack(pady=10)
        except Exception as e:
            ttk.Label(frm, text=f'Erro ao gerar analytics: {e}', foreground='red').pack()


def main():
    root = tk.Tk()
    app = DBViewerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
