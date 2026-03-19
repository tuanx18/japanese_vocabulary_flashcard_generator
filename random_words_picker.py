#!/usr/bin/env python3
"""Random Words Picker Tool
Single-file Python GUI using tkinter.
Features implemented:
- Landing window with Start Generate, Settings, Quit (layout as requested)
- Settings window:
* Word type checkboxes (n, v, adj, other/blank)
* Character/level checkboxes (H, K, N1..N5)
* Show/hide Romanji, Category, Level
* Count of words to pick (positive integer)
* English and Romanji font size settings
* Button to save settings and return
- Main window:
* Displays the selected words (sequence of random picks according to settings).
* Big responsive Japanese word centered on one line (font size reduced to fit width).
* Smaller English definition and Romanji below (visibility controllable, customizable font sizes).
* Back and Next buttons at bottom-left/right (140x50).
* The "Next" will advance and when a word is first revealed from the generated list it increments counter in word_counter.csv.
* The sequence respects filters and draws random unique choices.
* Alt key to reveal hidden items while held.
* Up Arrow key to toggle Reveal state.
- Reads dictionary.csv (expected columns: id,english,japanese,romanji,type,category,format,level)
- Maintains/creates word_counter.csv with columns: id,jp,en,type,counter
- Stores settings in settings.json in the app directory.
Usage: run this script with Python 3.8+ (tkinter included).
"""
import tkinter as tk
from tkinter import font, ttk, messagebox, filedialog
import csv, random, os, json, math, time
from pathlib import Path

APP_DIR = Path(__file__).parent
DICTIONARY_CSV = APP_DIR / 'dictionary.csv'
COUNTER_CSV = APP_DIR / 'word_counter.csv'
SETTINGS_JSON = APP_DIR / 'rw_picker_settings.json'

DEFAULT_SETTINGS = {
    'types': {'n': True, 'v': True, 'adj': True, 'other': True},
    'levels': {'H': True, 'K': True, 'N1': True, 'N2': True, 'N3': True, 'N4': True, 'N5': True},
    'show_romanji': True,
    'show_meaning': True,
    'show_category': True,
    'show_level': True,
    'pick_count': 1,
    'english_font_size': 16,
    'romanji_font_size': 14
}

def ensure_sample_dictionary():
    # Only create a sample dictionary if the file doesn't exist, without validation
    if not DICTIONARY_CSV.exists():
        print("dictionary.csv not found. Creating sample dictionary.")
        sample = [
            ['1','bookstore','書店','shoten','n','place','','N5'],
            ['2','to read','読む','yomu','v','','godan','N5'],
            ['3','love/romance','愛','ai','n','','','N4'],
            ['4','hair (katakana)','ヘア','hea','n','body','k','K'],
            ['5','to be careful','気をつける','ki wo tsukeru','v','','','N4'],
            ['6','beautiful','美しい','utsukushii','adj','','i','N3'],
        ]
        with DICTIONARY_CSV.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id','english','japanese','romanji','type','category','format','level'])
            writer.writerows(sample)
        print(f"Created sample dictionary at {DICTIONARY_CSV}")

def load_settings():
    if SETTINGS_JSON.exists():
        try:
            with SETTINGS_JSON.open('r', encoding='utf-8') as f:
                s = json.load(f)
                merged = DEFAULT_SETTINGS.copy()
                merged.update(s)
                merged['types'] = {**DEFAULT_SETTINGS['types'], **s.get('types', {})}
                merged['levels'] = {**DEFAULT_SETTINGS['levels'], **s.get('levels', {})}
                return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with SETTINGS_JSON.open('w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def read_dictionary():
    if not DICTIONARY_CSV.exists():
        ensure_sample_dictionary()
    try:
        rows = []
        with DICTIONARY_CSV.open('r', encoding='utf-8-sig') as f:  # Use utf-8-sig to handle BOM
            reader = csv.DictReader(f)
            print(f"Debug: Dictionary header: {reader.fieldnames}")  # Debug output
            for r in reader:
                # Normalize keys and values, provide defaults for missing columns
                row = {k.strip().lower(): (v.strip() if v is not None else '') for k,v in r.items()}
                # Ensure required fields have defaults
                row.setdefault('id', '')
                row.setdefault('japanese', '')
                row.setdefault('english', '')
                row.setdefault('romanji', '')
                row.setdefault('type', '')
                row.setdefault('category', '')
                row.setdefault('format', '')
                row.setdefault('level', '')
                rows.append(row)
        if not rows:
            raise ValueError("dictionary.csv is empty")
        return rows
    except Exception as e:
        messagebox.showerror('Error', f"Failed to read dictionary.csv: {e}")
        return []

def update_counter(entry):
    counters = {}
    if COUNTER_CSV.exists():
        with COUNTER_CSV.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                key = (r['id'], r['jp'], r['en'], r.get('type',''))
                counters[key] = int(r.get('counter', '0') or 0)
    key = (entry.get('id',''), entry.get('japanese',''), entry.get('english',''), entry.get('type',''))
    counters[key] = counters.get(key, 0) + 1
    with COUNTER_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id','jp','en','type','counter'])
        for (iid,jp,en,typ),cnt in counters.items():
            writer.writerow([iid,jp,en,typ,cnt])

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)
    def show_tip(self, e):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f'+{x}+{y}')
        label = tk.Label(self.tip, text=self.text, bg='yellow', relief='solid', borderwidth=1, padx=5, pady=3)
        label.pack()
    def hide_tip(self, e):
        if self.tip:
            self.tip.destroy()
            self.tip = None

class App:
    def __init__(self, root):
        self.root = root
        root.title('Random Words picker tool — Landing')
        root.state('zoomed')
        self.settings = load_settings()
        ensure_sample_dictionary()
        self.landing_frame = tk.Frame(root)
        self.landing_frame.pack(expand=True, fill='both')
        self._build_landing()
        self.dictionary = []
        self.sequence = []
        self.current_index = -1
        self.counted_ids = set()
        self.revealed = False
        self.alt_held = False
        self.start_time = None

    def _build_landing(self):
        for widget in self.landing_frame.winfo_children():
            widget.destroy()
        container = tk.Frame(self.landing_frame)
        container.place(relx=0.5, rely=0.5, anchor='center')
        btn_specs = [
            ('Start Generate', self.open_main_program),
            ('Setting', self.open_settings),
            ('Quit', self.root.quit)
        ]
        btn_height = 120
        btn_width = 400
        btn_gap = 30
        font_spec = ('Arial', 27)
        for i,(text, cmd) in enumerate(btn_specs):
            btn = tk.Button(container, text=text, command=cmd, width=1, height=1)
            btn.config(font=font_spec)
            btn.place(x=0, y=i*(btn_height+btn_gap), width=btn_width, height=btn_height)
        total_h = len(btn_specs)*btn_height + (len(btn_specs)-1)*btn_gap
        container.configure(width=btn_width, height=total_h)

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title('Settings')
        win.geometry('700x500')
        types_frame = tk.LabelFrame(win, text='Choose word type rolls')
        types_frame.pack(fill='x', padx=12, pady=8)
        self.type_vars = {}
        for key,label in [('n','Nouns (n)'),('v','Verbs (v)'),('adj','Adjectives (adj)'),('other','Other (blank)')]:
            var = tk.BooleanVar(value=self.settings['types'].get(key, True))
            cb = tk.Checkbutton(types_frame, text=label, variable=var)
            cb.pack(side='left', padx=10, pady=6)
            self.type_vars[key] = var
        levels_frame = tk.LabelFrame(win, text='Choose Japanese characters and difficulties')
        levels_frame.pack(fill='x', padx=12, pady=8)
        self.level_vars = {}
        for key in ['H','K','N1','N2','N3','N4','N5']:
            var = tk.BooleanVar(value=self.settings['levels'].get(key, True))
            cb = tk.Checkbutton(levels_frame, text=key, variable=var)
            cb.pack(side='left', padx=6, pady=6)
            self.level_vars[key] = var
        vis_frame = tk.LabelFrame(win, text='Display options')
        vis_frame.pack(fill='x', padx=12, pady=8)
        self.show_romanji_var = tk.BooleanVar(value=self.settings.get('show_romanji', True))
        self.show_cat_var = tk.BooleanVar(value=self.settings.get('show_category', True))
        self.show_level_var = tk.BooleanVar(value=self.settings.get('show_level', True))
        tk.Checkbutton(vis_frame, text='Show Romanji', variable=self.show_romanji_var).pack(side='left', padx=6)
        self.show_meaning_var = tk.BooleanVar(value=self.settings.get('show_meaning', True))
        tk.Checkbutton(vis_frame, text='Show Meaning', variable=self.show_meaning_var).pack(side='left', padx=6)
        tk.Checkbutton(vis_frame, text='Show Category', variable=self.show_cat_var).pack(side='left', padx=6)
        tk.Checkbutton(vis_frame, text='Show Level', variable=self.show_level_var).pack(side='left', padx=6)
        font_frame = tk.LabelFrame(win, text='Font sizes')
        font_frame.pack(fill='x', padx=12, pady=8)
        tk.Label(font_frame, text='English font size:').pack(side='left')
        self.english_font_var = tk.StringVar(value=str(self.settings.get('english_font_size', 16)))
        tk.Entry(font_frame, textvariable=self.english_font_var, width=6).pack(side='left', padx=6)
        tk.Label(font_frame, text='Romanji font size:').pack(side='left')
        self.romanji_font_var = tk.StringVar(value=str(self.settings.get('romanji_font_size', 14)))
        tk.Entry(font_frame, textvariable=self.romanji_font_var, width=6).pack(side='left', padx=6)
        pick_frame = tk.Frame(win)
        pick_frame.pack(fill='x', padx=12, pady=8)
        tk.Label(pick_frame, text='Number of words to pick (positive integer):').pack(side='left')
        self.pick_count_var = tk.StringVar(value=str(self.settings.get('pick_count',1)))
        tk.Entry(pick_frame, textvariable=self.pick_count_var, width=6).pack(side='left', padx=6)
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill='x', padx=12, pady=12)
        tk.Button(btn_frame, text='Save and Close', command=lambda: self._save_and_close_settings(win)).pack(side='left', padx=6)
        tk.Button(btn_frame, text='Load dictionary file...', command=self._choose_dictionary_file).pack(side='left', padx=6)

    def _choose_dictionary_file(self):
        path = filedialog.askopenfilename(title='Select dictionary.csv', filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8-sig') as fr:  # Use utf-8-sig to handle BOM
                content = fr.read()
                if not content.strip():
                    raise ValueError("Selected file is empty")
            with open(path, 'r', encoding='utf-8-sig') as fr, DICTIONARY_CSV.open('w', encoding='utf-8', newline='') as fw:
                fw.write(fr.read())
            self.dictionary = read_dictionary()
            messagebox.showinfo('Loaded', f'Dictionary loaded to {DICTIONARY_CSV}')
        except Exception as e:
            messagebox.showerror('Error', f"Failed to load dictionary: {e}")

    def copy_japanese_word(self):
        if not self.sequence or self.current_index < 0 or self.current_index >= len(self.sequence):
            return
        entry = self.sequence[self.current_index]
        jp = entry.get('japanese', '') or entry.get('jp', '')
        if jp:
            self.root.clipboard_clear()
            self.root.clipboard_append(jp)
            messagebox.showinfo('Copied', 'Japanese word copied to clipboard!')

    def _save_and_close_settings(self, win):
        try:
            pc = int(self.pick_count_var.get())
            if pc < 1:
                raise ValueError('pick_count must be >= 1')
            ef = int(self.english_font_var.get())
            if ef < 8:
                raise ValueError('English font size must be >= 8')
            rf = int(self.romanji_font_var.get())
            if rf < 8:
                raise ValueError('Romanji font size must be >= 8')
        except Exception:
            messagebox.showerror('Invalid input', 'Pick count and font sizes must be positive integers (font sizes >= 8).')
            return
        self.settings['types'] = {k: bool(v.get()) for k,v in self.type_vars.items()}
        self.settings['levels'] = {k: bool(v.get()) for k,v in self.level_vars.items()}
        self.settings['show_romanji'] = bool(self.show_romanji_var.get())
        self.settings['show_meaning'] = bool(self.show_meaning_var.get())
        self.settings['show_category'] = bool(self.show_cat_var.get())
        self.settings['show_level'] = bool(self.show_level_var.get())
        self.settings['pick_count'] = pc
        self.settings['english_font_size'] = ef
        self.settings['romanji_font_size'] = rf
        save_settings(self.settings)
        win.destroy()

    def open_main_program(self):
        try:
            self.dictionary = read_dictionary()
        except FileNotFoundError as e:
            messagebox.showerror('Missing dictionary.csv', str(e))
            return
        if not self.dictionary:
            messagebox.showwarning('No words', 'Dictionary is empty or could not be loaded.')
            return
        filtered = self._apply_filters(self.dictionary)
        if not filtered:
            messagebox.showwarning('No words', 'No words match your current filters. Adjust settings or load a different dictionary.')
            return
        count = int(self.settings.get('pick_count', 1))
        if count <= len(filtered):
            picks = random.sample(filtered, count)
        else:
            picks = [random.choice(filtered) for _ in range(count)]
        self.sequence = picks
        self.current_index = 0
        self.counted_ids = set()
        self.landing_frame.destroy()
        self._build_main_window()

    def _apply_filters(self, rows):
        types_allowed = {k for k,v in self.settings['types'].items() if v}
        levels_allowed = {k for k,v in self.settings['levels'].items() if v}
        out = []
        for r in rows:
            typ = (r.get('type') or '').strip()
            if typ == '':
                typ_key = 'other'
            elif typ.lower() == 'adj':
                typ_key = 'adj'
            elif typ.lower() == 'v':
                typ_key = 'v'
            elif typ.lower() == 'n':
                typ_key = 'n'
            else:
                typ_key = typ if typ in types_allowed else 'other'
            if typ_key not in types_allowed:
                continue
            level = (r.get('level') or '').strip()
            if level == '':
                continue
            if level not in levels_allowed:
                continue
            out.append(r)
        return out

    def _build_main_window(self):
        self.root.title('Random Words picker tool — Main')
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        self.timer_label = tk.Label(self.main_frame, text='Time: 0s', font=('Arial',12))
        self.timer_label.pack(side='top', pady=10)
        self.display_canvas = tk.Canvas(self.main_frame, bg='white')
        self.display_canvas.pack(expand=True, fill='both', padx=20, pady=20)
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.pack(fill='x', padx=20)
        self.english_label = tk.Label(self.info_frame, text='', font=('Arial', self.settings.get('english_font_size', 16)))
        self.english_label.pack(pady=(6,2))
        self.romanji_label = tk.Label(self.info_frame, text='', font=('Arial', self.settings.get('romanji_font_size', 14)))
        self.romanji_label.pack(pady=(2,8))
        self.footer_frame = tk.Frame(self.main_frame)
        self.footer_frame.pack(fill='x', padx=20, pady=(0,60))
        self.meta_label = tk.Label(self.footer_frame, text='', anchor='w', justify='left', font=('Arial',12))
        self.meta_label.pack(side='left')
        bottom_left_frame = tk.Frame(self.main_frame)
        bottom_left_frame.place(relx=0.0, rely=1.0, anchor='sw')
        btn_back = tk.Button(bottom_left_frame, text='Back', command=self.on_back)
        btn_back.config(width=14, height=2)
        btn_back.pack(side='left')
        ToolTip(btn_back, 'Go to previous word (Backspace or <)')
        btn_menu = tk.Button(bottom_left_frame, text='Main Menu', command=self.return_to_landing)
        btn_menu.config(width=14, height=2)
        btn_menu.pack(side='left')
        bottom_right_frame = tk.Frame(self.main_frame)
        bottom_right_frame.place(relx=1.0, rely=1.0, anchor='se')
        btn_copy = tk.Button(bottom_right_frame, text='Copy', command=self.copy_japanese_word)
        btn_copy.config(width=14, height=2)
        btn_copy.pack(side='left')
        ToolTip(btn_copy, 'Copy the Japanese word to clipboard')
        self.reveal_button = tk.Button(bottom_right_frame, text='Reveal', command=self.toggle_reveal)
        self.reveal_button.config(width=14, height=2)
        self.reveal_button.pack(side='left')
        btn_next = tk.Button(bottom_right_frame, text='Next', command=self.on_next)
        btn_next.config(width=14, height=2)
        btn_next.pack(side='left')
        ToolTip(btn_next, 'Go to next word (Enter or >)')
        self.display_canvas.bind('<Configure>', lambda e: self._render_current_word())
        self.bind_keys()
        self._render_current_word()

    def bind_keys(self):
        self.root.bind('<Return>', lambda e: self.on_next())
        self.root.bind('<greater>', lambda e: self.on_next())
        self.root.bind('<BackSpace>', lambda e: self.on_back())
        self.root.bind('<less>', lambda e: self.on_back())
        self.root.bind('<Up>', lambda e: self.toggle_reveal())
        self.root.bind('<Alt_L>', lambda e: self.on_alt_press())
        self.root.bind('<KeyRelease-Alt_L>', lambda e: self.on_alt_release())

    def unbind_keys(self):
        self.root.unbind('<Return>')
        self.root.unbind('<greater>')
        self.root.unbind('<BackSpace>')
        self.root.unbind('<less>')
        self.root.unbind('<Up>')
        self.root.unbind('<Alt_L>')
        self.root.unbind('<KeyRelease-Alt_L>')

    def on_alt_press(self):
        self.alt_held = True
        self._render_current_word()

    def on_alt_release(self):
        self.alt_held = False
        self._render_current_word()

    def return_to_landing(self):
        self.unbind_keys()
        self.main_frame.destroy()
        self.sequence = []
        self.current_index = -1
        self.counted_ids = set()
        self.revealed = False
        self.alt_held = False
        self.start_time = None
        self.landing_frame = tk.Frame(self.root)
        self.landing_frame.pack(expand=True, fill='both')
        self._build_landing()
        self.root.title('Random Words picker tool — Landing')

    def toggle_reveal(self):
        self.revealed = not self.revealed
        if hasattr(self, 'reveal_button'):
            self.reveal_button.config(text='Hide' if self.revealed else 'Reveal')
        self._render_current_word()

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.timer_label.config(text=f'Time: {elapsed}s')
            self.root.after(1000, self.update_timer)

    def _render_current_word(self):
        self.display_canvas.delete('all')
        if not self.sequence:
            self.display_canvas.create_text(10,10, anchor='nw', text='No words generated yet. Use Settings to adjust filters and Start Generate.', font=('Arial',14))
            return
        if self.current_index < 0 or self.current_index >= len(self.sequence):
            return
        entry = self.sequence[self.current_index]
        jp = entry.get('japanese','') or entry.get('jp','')
        en = entry.get('english','') or entry.get('en','')
        romanji = entry.get('romanji','') or entry.get('romaji','') or ''
        typ = entry.get('type','') or ''
        cat = entry.get('category','') or 'N/A'
        lvl = entry.get('level','') or ''
        word_id = entry.get('id','') or ''
        canvas_width = max(200, self.display_canvas.winfo_width()-40)
        canvas_height = max(100, self.display_canvas.winfo_height()-40)
        test_font = font.Font(family='Arial', size=100, weight='bold')
        txt = jp or '(no jp)'
        max_size = 200
        min_size = 18
        lo, hi = min_size, max_size
        while lo <= hi:
            mid = (lo+hi)//2
            test_font.config(size=mid)
            w = test_font.measure(txt)
            h = test_font.metrics('linespace')
            if w <= canvas_width and h <= canvas_height*0.6:
                lo = mid + 1
                chosen = mid
            else:
                hi = mid - 1
        chosen_size = max(min_size, min(chosen if 'chosen' in locals() else 32, max_size))
        display_font = font.Font(family='Arial', size=chosen_size, weight='bold')
        cx = self.display_canvas.winfo_width()//2
        cy = self.display_canvas.winfo_height()//2 - 30
        self.display_canvas.create_text(cx, cy, text=txt, font=display_font, anchor='center')
        show_meaning = self.settings.get('show_meaning', True) or self.revealed or self.alt_held
        show_romanji = self.settings.get('show_romanji', True) or self.revealed or self.alt_held
        if show_meaning:
            self.english_label.config(text=en, font=('Arial', self.settings.get('english_font_size', 16)))
            self.english_label.pack_configure()
        else:
            self.english_label.config(text='')
            self.english_label.pack_forget()
        if show_romanji:
            self.romanji_label.config(text=romanji, font=('Arial', self.settings.get('romanji_font_size', 14)))
            self.romanji_label.pack_configure()
        else:
            self.romanji_label.config(text='')
            self.romanji_label.pack_forget()
        meta_parts = []
        if word_id:
            meta_parts.append(f'ID: {word_id}')
        if typ and self.settings.get('show_category', True):
            meta_parts.append(f'Type: {typ}')
        meta_parts.append(f'Category: {cat}')
        if lvl and self.settings.get('show_level', True):
            meta_parts.append(f'Level: {lvl}')
        self.meta_label.config(text='\n'.join(meta_parts))
        self.start_time = time.time()
        self.update_timer()

    def on_next(self):
        if not self.sequence:
            return
        if self.current_index not in self.counted_ids:
            try:
                update_counter(self.sequence[self.current_index])
            except Exception as e:
                messagebox.showwarning('Counter error', f'Could not update counter: {e}')
            self.counted_ids.add(self.current_index)
        self.revealed = False
        if hasattr(self, 'reveal_button'):
            self.reveal_button.config(text='Reveal')
        if self.current_index < len(self.sequence)-1:
            self.current_index += 1
            self._render_current_word()
        else:
            messagebox.showinfo('End', 'You have reached the last word in the generated sequence. You can generate another batch from landing.')

    def on_back(self):
        if not self.sequence:
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.revealed = False
            if hasattr(self, 'reveal_button'):
                self.reveal_button.config(text='Reveal')
            self._render_current_word()
        else:
            messagebox.showinfo('Start', 'This is the first word in the sequence.')

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()