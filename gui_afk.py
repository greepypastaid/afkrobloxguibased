"""
gui_afk.py
==========
Antarmuka Grafis (GUI) Bersih, Minimalis, dan Profesional.
Desain Default Putih (Light Theme) tanpa emoji/karakter rusak,
proporsi pas tanpa ruang kosong berlebih, dan alur kerja yang sangat simpel.
"""

import time
from pathlib import Path
from typing import Optional, List, Tuple

import customtkinter as ctk

from core.constants import (
    AFKMode,
    WalkPattern,
    MouseButton,
    EngineState
)
from core.config import AFKConfig
from core.win32_api import get_open_windows, is_roblox_window, find_roblox_hwnd
from afk_engine import AFKEngine

try:
    import keyboard
    HAS_KEYBOARD_HOOK = True
except ImportError:
    HAS_KEYBOARD_HOOK = False

CONFIG_PATH = Path("config.json")

# Tema Default: Light Mode (Putih Bersih)
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")


class ModernAFKApp(ctk.CTk):
    """Aplikasi GUI Roblox AFK Bot Bersih dan Minimalis."""

    # Palet Warna Light Minimalis
    COLOR_BG = "#f1f5f9"
    COLOR_CARD = "#ffffff"
    COLOR_BORDER = "#cbd5e1"
    COLOR_GREEN = "#10b981"
    COLOR_GREEN_HOVER = "#059669"
    COLOR_RED = "#ef4444"
    COLOR_RED_HOVER = "#dc2626"
    COLOR_TEXT = "#0f172a"
    COLOR_MUTED = "#64748b"
    COLOR_INPUT = "#f8fafc"

    def __init__(self):
        super().__init__()

        # Konfigurasi Window Shell (Proporsional & Rapi)
        self.title("Roblox AFK Bot")
        self.geometry("480x520")
        self.minsize(460, 480)
        self.resizable(False, False)
        self.configure(fg_color=self.COLOR_BG)

        # 1. Muat Konfigurasi
        self.config = AFKConfig.load_from_file(CONFIG_PATH)

        # 2. Inisialisasi Engine
        self.engine = AFKEngine(self.config)
        self.engine.on_log = self._thread_safe_log
        self.engine.on_state_change = self._thread_safe_state_change
        self.engine.on_stats_update = self._thread_safe_stats_update

        self.window_list: List[Tuple[int, str]] = []
        self._slider_vars: dict = {}
        self._log_visible: bool = False

        # 3. Bangun Tampilan
        self._build_ui()
        self._refresh_window_list()
        self._populate_ui_from_config()
        self._register_hotkeys()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------------------------------------------------
    # UI LAYOUT
    # -------------------------------------------------------------
    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=14, pady=12)

        self._build_header(container)
        self._build_target_card(container)
        self._build_mode_selector(container)
        self._build_settings_card(container)
        self._build_action_buttons(container)
        self._build_status_bar(container)

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        """Header simpel dengan judul dan switch Always on Top."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        title_lbl = ctk.CTkLabel(
            header,
            text="Roblox AFK Bot",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        title_lbl.pack(side="left")

        self.switch_always_top = ctk.CTkSwitch(
            header,
            text="Always on Top",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_MUTED,
            progress_color=self.COLOR_GREEN,
            command=self._toggle_always_on_top
        )
        self.switch_always_top.pack(side="right")

    def _build_target_card(self, parent: ctk.CTkFrame) -> None:
        """Pilihan Game Target dan Background Multitasking."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER,
            corner_radius=8
        )
        card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Baris Jendela
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            row,
            text="Game Target:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLOR_TEXT
        ).pack(side="left", padx=(0, 6))

        self.opt_window = ctk.CTkOptionMenu(
            row,
            values=["(Mencari game...)"],
            fg_color=self.COLOR_INPUT,
            button_color="#cbd5e1",
            button_hover_color="#94a3b8",
            text_color=self.COLOR_TEXT,
            dropdown_fg_color=self.COLOR_CARD,
            dropdown_text_color=self.COLOR_TEXT,
            dropdown_hover_color=self.COLOR_INPUT,
            font=ctk.CTkFont(size=11),
            height=28
        )
        self.opt_window.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            row,
            text="Refresh",
            width=55,
            height=28,
            fg_color="#e2e8f0",
            hover_color="#cbd5e1",
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._refresh_window_list
        ).pack(side="right")

        # Toggle Multitasking
        self.switch_bg_mode = ctk.CTkSwitch(
            inner,
            text="Background Mode (Multitasking / Kerja sambil AFK)",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT,
            progress_color=self.COLOR_GREEN
        )
        self.switch_bg_mode.pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text="Catatan: Roblox boleh tertimpa aplikasi lain, tapi jangan di-minimize ke taskbar.",
            font=ctk.CTkFont(size=9),
            text_color=self.COLOR_MUTED
        ).pack(anchor="w", pady=(3, 0))

    def _build_mode_selector(self, parent: ctk.CTkFrame) -> None:
        """Pill selector mode tanpa emoji berantakan."""
        self.mode_tabs = [
            "Auto Fish",
            "Walk & Jump",
            "Auto Clicker",
            "Key Spammer"
        ]

        self.seg_mode = ctk.CTkSegmentedButton(
            parent,
            values=self.mode_tabs,
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color=self.COLOR_GREEN,
            selected_hover_color=self.COLOR_GREEN_HOVER,
            unselected_color="#e2e8f0",
            unselected_hover_color="#cbd5e1",
            text_color=self.COLOR_TEXT,
            height=30,
            command=self._on_tab_mode_selected
        )
        self.seg_mode.set(self.mode_tabs[0])
        self.seg_mode.pack(fill="x", pady=(0, 8))

    def _build_settings_card(self, parent: ctk.CTkFrame) -> None:
        """Panel pengaturan yang menyesuaikan dengan mode."""
        self.card_settings = ctk.CTkFrame(
            parent,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER,
            corner_radius=8
        )
        self.card_settings.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(self.card_settings, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        self.panel_fish = ctk.CTkFrame(inner, fg_color="transparent")
        self.panel_walk = ctk.CTkFrame(inner, fg_color="transparent")
        self.panel_clicker = ctk.CTkFrame(inner, fg_color="transparent")
        self.panel_spammer = ctk.CTkFrame(inner, fg_color="transparent")

        self._build_panel_fish()
        self._build_panel_walk()
        self._build_panel_clicker()
        self._build_panel_spammer()

        self.panel_fish.pack(fill="x")

    def _create_slider_row(
        self,
        parent: ctk.CTkFrame,
        label_text: str,
        var_key: str,
        from_: float,
        to_: float,
        default_val: float,
        unit: str = "s",
        decimals: int = 1
    ) -> ctk.CTkSlider:
        """Baris slider bersih dengan indikator angka."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(fill="x")

        ctk.CTkLabel(
            info,
            text=label_text,
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT
        ).pack(side="left")

        val_badge = ctk.CTkLabel(
            info,
            text=f"{default_val:.{decimals}f}{unit}",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=self.COLOR_TEXT,
            fg_color=self.COLOR_INPUT,
            corner_radius=4,
            width=50,
            height=18
        )
        val_badge.pack(side="right")

        def on_change(val: float):
            val_badge.configure(text=f"{val:.{decimals}f}{unit}")

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to_,
            number_of_steps=int((to_ - from_) / (0.1 if decimals == 1 else 0.02)),
            progress_color=self.COLOR_GREEN,
            button_color=self.COLOR_GREEN,
            button_hover_color=self.COLOR_GREEN_HOVER,
            command=on_change,
            height=12
        )
        slider.set(default_val)
        slider.pack(fill="x", pady=(1, 0))

        self._slider_vars[var_key] = (slider, val_badge, unit, decimals)
        return slider

    def _build_panel_fish(self) -> None:
        p = self.panel_fish
        self._create_slider_row(p, "Durasi Lempar Joran:", "fish_cast", 0.1, 2.5, 0.6, "s", 1)
        self._create_slider_row(p, "Waktu Tunggu Ikan:", "fish_wait", 0.5, 8.0, 3.2, "s", 1)
        self._create_slider_row(p, "Durasi Tarik Ikan:", "fish_reel_dur", 1.0, 10.0, 4.2, "s", 1)

        self.switch_fish_space = ctk.CTkSwitch(
            p,
            text="Tekan Spasi saat menarik",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_MUTED,
            progress_color=self.COLOR_GREEN
        )
        self.switch_fish_space.pack(anchor="w", pady=(4, 1))

    def _build_panel_walk(self) -> None:
        p = self.panel_walk

        row_pat = ctk.CTkFrame(p, fg_color="transparent")
        row_pat.pack(fill="x", pady=2)

        ctk.CTkLabel(row_pat, text="Pola Jalan:", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT).pack(side="left", padx=(0, 6))

        self.walk_patterns = [
            (WalkPattern.display_name(WalkPattern.PING_PONG), WalkPattern.PING_PONG),
            (WalkPattern.display_name(WalkPattern.SQUARE), WalkPattern.SQUARE),
            (WalkPattern.display_name(WalkPattern.LEFT_RIGHT), WalkPattern.LEFT_RIGHT),
            (WalkPattern.display_name(WalkPattern.RANDOM), WalkPattern.RANDOM),
        ]

        self.opt_walk_pattern = ctk.CTkOptionMenu(
            row_pat,
            values=[name for name, _ in self.walk_patterns],
            fg_color=self.COLOR_INPUT,
            button_color="#cbd5e1",
            button_hover_color="#94a3b8",
            text_color=self.COLOR_TEXT,
            dropdown_fg_color=self.COLOR_CARD,
            dropdown_text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(size=11),
            height=26
        )
        self.opt_walk_pattern.pack(side="left", fill="x", expand=True)

        self._create_slider_row(p, "Jeda Antar Aksi:", "walk_int", 2.0, 20.0, 6.0, "s", 1)
        self._create_slider_row(p, "Peluang Melompat:", "walk_jump", 0, 100, 80, "%", 0)

    def _build_panel_clicker(self) -> None:
        p = self.panel_clicker

        row_btn = ctk.CTkFrame(p, fg_color="transparent")
        row_btn.pack(fill="x", pady=2)

        ctk.CTkLabel(row_btn, text="Tombol Mouse:", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT).pack(side="left", padx=(0, 6))

        self.seg_click_btn = ctk.CTkSegmentedButton(
            row_btn,
            values=["Klik Kiri", "Klik Kanan"],
            selected_color=self.COLOR_GREEN,
            selected_hover_color=self.COLOR_GREEN_HOVER,
            unselected_color="#e2e8f0",
            text_color=self.COLOR_TEXT,
            height=26
        )
        self.seg_click_btn.set("Klik Kiri")
        self.seg_click_btn.pack(side="left", fill="x", expand=True)

        self._create_slider_row(p, "Interval Klik:", "click_int", 0.05, 2.0, 0.25, "s", 2)

    def _build_panel_spammer(self) -> None:
        p = self.panel_spammer

        row_key = ctk.CTkFrame(p, fg_color="transparent")
        row_key.pack(fill="x", pady=2)

        ctk.CTkLabel(row_key, text="Tombol Keyboard:", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT).pack(side="left", padx=(0, 6))

        self.entry_spam_key = ctk.CTkEntry(
            row_key,
            width=50,
            height=26,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=self.COLOR_INPUT,
            border_color="#cbd5e1",
            text_color=self.COLOR_GREEN
        )
        self.entry_spam_key.insert(0, "e")
        self.entry_spam_key.pack(side="left")

        self._create_slider_row(p, "Interval Tekan:", "spam_int", 0.05, 2.0, 0.50, "s", 2)

    def _build_action_buttons(self, parent: ctk.CTkFrame) -> None:
        """Tombol Mulai dan Berhenti yang kontras dan jelas."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))

        self.btn_start = ctk.CTkButton(
            row,
            text="Mulai (F6)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.COLOR_GREEN,
            hover_color=self.COLOR_GREEN_HOVER,
            text_color="#ffffff",
            height=38,
            corner_radius=6,
            command=self.start_afk
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_stop = ctk.CTkButton(
            row,
            text="Berhenti (F7)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.COLOR_RED,
            hover_color=self.COLOR_RED_HOVER,
            text_color="#ffffff",
            height=38,
            corner_radius=6,
            state="disabled",
            command=self.stop_afk
        )
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _build_status_bar(self, parent: ctk.CTkFrame) -> None:
        """Status bar ringkas: durasi, counter, dan log toggle."""
        bar = ctk.CTkFrame(
            parent,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER,
            corner_radius=8
        )
        bar.pack(fill="x")

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        # Baris Metrik & Status
        top_bar = ctk.CTkFrame(inner, fg_color="transparent")
        top_bar.pack(fill="x")

        self.lbl_status_text = ctk.CTkLabel(
            top_bar,
            text="Status: Standby",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLOR_MUTED
        )
        self.lbl_status_text.pack(side="left")

        self.lbl_time = ctk.CTkLabel(
            top_bar,
            text="00:00:00",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=self.COLOR_MUTED
        )
        self.lbl_time.pack(side="left", padx=(10, 0))

        self.lbl_counter = ctk.CTkLabel(
            top_bar,
            text="Total: 0",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        self.lbl_counter.pack(side="right")

        # Baris Bawah: Ticker log + Tombol Lihat Log
        sub_bar = ctk.CTkFrame(inner, fg_color="transparent")
        sub_bar.pack(fill="x", pady=(4, 0))

        self.lbl_ticker = ctk.CTkLabel(
            sub_bar,
            text="Siap digunakan.",
            font=ctk.CTkFont(size=10),
            text_color=self.COLOR_MUTED,
            anchor="w"
        )
        self.lbl_ticker.pack(side="left", fill="x", expand=True)

        self.btn_toggle_log = ctk.CTkButton(
            sub_bar,
            text="Log",
            width=40,
            height=20,
            fg_color="#e2e8f0",
            hover_color="#cbd5e1",
            text_color=self.COLOR_TEXT,
            font=ctk.CTkFont(size=9),
            command=self._toggle_log_drawer
        )
        self.btn_toggle_log.pack(side="right")

        # Kotak Log Drawer (tersembunyi secara default)
        self.txt_log = ctk.CTkTextbox(
            inner,
            height=70,
            fg_color="#f8fafc",
            text_color="#1e293b",
            font=ctk.CTkFont(family="Consolas", size=10),
            border_width=1,
            border_color="#e2e8f0",
            corner_radius=4
        )

    # -------------------------------------------------------------
    # LOGIC & EVENT HANDLERS
    # -------------------------------------------------------------
    def _toggle_log_drawer(self) -> None:
        self._log_visible = not self._log_visible
        if self._log_visible:
            self.txt_log.pack(fill="x", pady=(6, 0))
            self.btn_toggle_log.configure(text="Tutup")
            self.geometry("480x590")
        else:
            self.txt_log.pack_forget()
            self.btn_toggle_log.configure(text="Log")
            self.geometry("480x510")

    def _on_tab_mode_selected(self, value: str) -> None:
        self.panel_fish.pack_forget()
        self.panel_walk.pack_forget()
        self.panel_clicker.pack_forget()
        self.panel_spammer.pack_forget()

        if value == "Auto Fish":
            self.panel_fish.pack(fill="x")
            self.lbl_counter.configure(text="Ikan: 0")
        elif value == "Walk & Jump":
            self.panel_walk.pack(fill="x")
            self.lbl_counter.configure(text="Langkah: 0")
        elif value == "Auto Clicker":
            self.panel_clicker.pack(fill="x")
            self.lbl_counter.configure(text="Klik: 0")
        elif value == "Key Spammer":
            self.panel_spammer.pack(fill="x")
            self.lbl_counter.configure(text="Tekan: 0")

    def _refresh_window_list(self) -> None:
        """Mengambil daftar jendela dan memprioritaskan game Roblox asli."""
        try:
            self.window_list = get_open_windows()
        except Exception:
            self.window_list = []

        # Cek HWND Roblox presisi via find_roblox_hwnd
        detected_roblox = find_roblox_hwnd()
        if detected_roblox and not any(h == detected_roblox for h, _ in self.window_list):
            self.window_list.insert(0, (detected_roblox, "Roblox"))

        options = []
        roblox_choice = None
        for hwnd, title in self.window_list:
            # Saring jendela IDE/editor jika bukan Roblox
            if not is_roblox_window(title, hwnd) and any(k in title.lower() for k in ["antigravity", "ide", "vscode", "code"]):
                continue

            label = f"[{hwnd}] {title}"
            options.append(label)
            if (hwnd == detected_roblox or is_roblox_window(title, hwnd)) and roblox_choice is None:
                roblox_choice = label

        if not options:
            options = ["(Game tidak terdeteksi)"]

        self.opt_window.configure(values=options)
        if roblox_choice:
            self.opt_window.set(roblox_choice)
            self._log(f"Jendela Roblox terdeteksi: {roblox_choice}")
        else:
            self.opt_window.set(options[0])

    def _toggle_always_on_top(self) -> None:
        self.attributes("-topmost", bool(self.switch_always_top.get()))

    def _populate_ui_from_config(self) -> None:
        cfg = self.config

        mode_map = {
            AFKMode.AUTO_FISH: "Auto Fish",
            AFKMode.WALK_JUMP: "Walk & Jump",
            AFKMode.AUTO_CLICKER: "Auto Clicker",
            AFKMode.KEY_SPAMMER: "Key Spammer"
        }
        tab_name = mode_map.get(cfg.mode, "Auto Fish")
        self.seg_mode.set(tab_name)
        self._on_tab_mode_selected(tab_name)

        if cfg.background_mode:
            self.switch_bg_mode.select()
        else:
            self.switch_bg_mode.deselect()

        self._set_slider("fish_cast", cfg.fish_cast_duration)
        self._set_slider("fish_wait", cfg.fish_wait_bite)
        self._set_slider("fish_reel_dur", cfg.fish_reel_duration)
        if cfg.fish_tap_space:
            self.switch_fish_space.select()
        else:
            self.switch_fish_space.deselect()

        self._set_slider("walk_int", cfg.walk_interval)
        self._set_slider("walk_jump", cfg.jump_chance)
        for name, pat_enum in self.walk_patterns:
            if pat_enum == cfg.pattern:
                self.opt_walk_pattern.set(name)
                break

        self._set_slider("click_int", cfg.clicker_interval)
        self.seg_click_btn.set("Klik Kanan" if cfg.clicker_button == MouseButton.RIGHT else "Klik Kiri")

        self._set_slider("spam_int", cfg.spam_interval)
        self.entry_spam_key.delete(0, "end")
        self.entry_spam_key.insert(0, cfg.spam_key)

    def _set_slider(self, key: str, val: float) -> None:
        if key in self._slider_vars:
            slider, badge, unit, decimals = self._slider_vars[key]
            slider.set(val)
            badge.configure(text=f"{val:.{decimals}f}{unit}")

    def _sync_config_from_ui(self) -> None:
        cfg = self.config

        selected_text = self.opt_window.get()
        matched = False
        for hwnd, title in self.window_list:
            if f"[{hwnd}]" in selected_text:
                cfg.target_hwnd = hwnd
                cfg.target_title = title
                matched = True
                break

        if not matched or not cfg.target_hwnd:
            roblox_hwnd = find_roblox_hwnd()
            if roblox_hwnd:
                cfg.target_hwnd = roblox_hwnd
                cfg.target_title = "Roblox"

        active_tab = self.seg_mode.get()
        if active_tab == "Auto Fish":
            cfg.mode = AFKMode.AUTO_FISH
        elif active_tab == "Walk & Jump":
            cfg.mode = AFKMode.WALK_JUMP
        elif active_tab == "Auto Clicker":
            cfg.mode = AFKMode.AUTO_CLICKER
        elif active_tab == "Key Spammer":
            cfg.mode = AFKMode.KEY_SPAMMER

        cfg.background_mode = bool(self.switch_bg_mode.get())

        if "fish_cast" in self._slider_vars:
            cfg.fish_cast_duration = float(self._slider_vars["fish_cast"][0].get())
        if "fish_wait" in self._slider_vars:
            cfg.fish_wait_bite = float(self._slider_vars["fish_wait"][0].get())
        if "fish_reel_dur" in self._slider_vars:
            cfg.fish_reel_duration = float(self._slider_vars["fish_reel_dur"][0].get())
        cfg.fish_tap_space = bool(self.switch_fish_space.get())

        if "walk_int" in self._slider_vars:
            cfg.walk_interval = float(self._slider_vars["walk_int"][0].get())
        if "walk_jump" in self._slider_vars:
            cfg.jump_chance = int(float(self._slider_vars["walk_jump"][0].get()))

        pat_text = self.opt_walk_pattern.get()
        for name, pat_enum in self.walk_patterns:
            if name == pat_text:
                cfg.pattern = pat_enum
                break

        if "click_int" in self._slider_vars:
            cfg.clicker_interval = float(self._slider_vars["click_int"][0].get())
        cfg.clicker_button = MouseButton.RIGHT if "Kanan" in self.seg_click_btn.get() else MouseButton.LEFT

        if "spam_int" in self._slider_vars:
            cfg.spam_interval = float(self._slider_vars["spam_int"][0].get())
        cfg.spam_key = self.entry_spam_key.get().strip() or "e"

        cfg.save_to_file(CONFIG_PATH)

    def _register_hotkeys(self) -> None:
        if not HAS_KEYBOARD_HOOK:
            return
        try:
            keyboard.add_hotkey('f6', self.start_afk)
            keyboard.add_hotkey('f7', self.stop_afk)
        except Exception:
            pass

    def start_afk(self) -> None:
        if self.engine.is_running():
            return
        self._sync_config_from_ui()
        self.engine.start()

        self.btn_start.configure(state="disabled", fg_color="#cbd5e1")
        self.btn_stop.configure(state="normal", fg_color=self.COLOR_RED)

    def stop_afk(self) -> None:
        if not self.engine.is_running():
            return
        self.engine.stop()

        self.btn_start.configure(state="normal", fg_color=self.COLOR_GREEN)
        self.btn_stop.configure(state="disabled", fg_color="#cbd5e1")

    def _thread_safe_log(self, message: str) -> None:
        self.after(0, self._log, message)

    def _log(self, message: str) -> None:
        now_str = time.strftime("%H:%M:%S")
        clean_msg = message.replace("🎣 ", "").replace("⏳ ", "").replace("🐟 ", "").replace("✅ ", "").replace("🛑 ", "").replace("🚶 ", "").replace("🦘 ", "").replace("💤 ", "").replace("🎯 ", "").replace("✨ ", "").replace("⚠️ ", "").replace("🔍 ", "").replace("🚀 ", "")
        self.lbl_ticker.configure(text=clean_msg)
        self.txt_log.insert("end", f"[{now_str}] {clean_msg}\n")
        self.txt_log.see("end")

    def _thread_safe_state_change(self, state_str: str) -> None:
        self.after(0, self._update_state_ui, state_str)

    def _update_state_ui(self, state_str: str) -> None:
        if state_str == EngineState.RUNNING.value:
            bg_tag = " (Background)" if self.config.background_mode else " (Foreground)"
            self.lbl_status_text.configure(
                text=f"Status: Aktif {bg_tag}",
                text_color=self.COLOR_GREEN
            )
            self.btn_start.configure(state="disabled", fg_color="#cbd5e1")
            self.btn_stop.configure(state="normal", fg_color=self.COLOR_RED)
        elif state_str == EngineState.COUNTDOWN.value:
            self.lbl_status_text.configure(
                text="Status: Bersiap mulai...",
                text_color="#d97706"
            )
            self.btn_start.configure(state="disabled", fg_color="#cbd5e1")
            self.btn_stop.configure(state="normal", fg_color=self.COLOR_RED)
        else:
            self.lbl_status_text.configure(
                text="Status: Standby",
                text_color=self.COLOR_MUTED
            )
            self.btn_start.configure(state="normal", fg_color=self.COLOR_GREEN)
            self.btn_stop.configure(state="disabled", fg_color="#cbd5e1")

    def _thread_safe_stats_update(self, elapsed: float, primary: int, secondary: int) -> None:
        self.after(0, self._update_stats_ui, elapsed, primary, secondary)

    def _update_stats_ui(self, elapsed: float, primary: int, secondary: int) -> None:
        h = int(elapsed // 3600)
        m = int((elapsed % 3600) // 60)
        s = int(elapsed % 60)
        self.lbl_time.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

        mode = self.config.mode
        if mode == AFKMode.AUTO_FISH:
            self.lbl_counter.configure(text=f"Ikan: {primary}")
        elif mode == AFKMode.WALK_JUMP:
            self.lbl_counter.configure(text=f"Langkah: {primary}")
        elif mode == AFKMode.AUTO_CLICKER:
            self.lbl_counter.configure(text=f"Klik: {primary}")
        elif mode == AFKMode.KEY_SPAMMER:
            self.lbl_counter.configure(text=f"Tekan: {primary}")

    def on_close(self) -> None:
        if self.engine.is_running():
            self.engine.stop()
        self._sync_config_from_ui()
        if HAS_KEYBOARD_HOOK:
            try:
                keyboard.unhook_all()
            except Exception:
                pass
        self.destroy()


def run_gui() -> None:
    app = ModernAFKApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
