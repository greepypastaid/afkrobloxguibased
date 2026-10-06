"""
core.controllers
================
Controller pengirim input mouse dan keyboard ke sistem operasi Windows.
Mendukung mode Background (PostMessageW) dan Foreground (DirectInput ScanCodes).
"""

import time
import threading
import ctypes
from ctypes import wintypes
from typing import Optional, Set

from .constants import (
    WM_KEYDOWN,
    WM_KEYUP,
    WM_CHAR,
    WM_MOUSEMOVE,
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WM_RBUTTONDOWN,
    WM_RBUTTONUP,
    MK_LBUTTON,
    MK_RBUTTON,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    INPUT_KEYBOARD,
    INPUT_MOUSE,
    SCAN_CODES,
    VK_CODES,
    MouseButton
)

# Mouse event flags untuk SendInput
MOUSEEVENTF_LEFTDOWN  = 0x0002
MOUSEEVENTF_LEFTUP    = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP   = 0x0010
from .win32_api import (
    user32,
    kernel32,
    is_valid_hwnd,
    ensure_window_restored,
    get_window_client_center,
    get_window_screen_center,
    Input,
    KeyBdInput,
    MouseInput
)

# Integrasi opsional pydirectinput
try:
    import pydirectinput
    pydirectinput.PAUSE = 0.02
    pydirectinput.FAILSAFE = False
    HAS_PYDIRECTINPUT = True
except ImportError:
    HAS_PYDIRECTINPUT = False


class BackgroundController:
    """
    Mengirim input mouse dan keyboard langsung ke antrian pesan jendela target
    menggunakan PostMessageW Windows API.
    Memungkinkan multitasking tanpa mengalihkan fokus mouse/keyboard pengguna.
    """

    @staticmethod
    def click(
        hwnd: int,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: MouseButton = MouseButton.LEFT,
        hold_time: float = 0.05
    ) -> None:
        """Mengirim klik mouse ke koordinat client jendela target."""
        if not is_valid_hwnd(hwnd):
            return

        ensure_window_restored(hwnd)
        if x is None or y is None:
            x, y = get_window_client_center(hwnd)

        lparam = (y << 16) | (x & 0xFFFF)
        is_left = (button == MouseButton.LEFT or button == "left")
        down_msg = WM_LBUTTONDOWN if is_left else WM_RBUTTONDOWN
        up_msg = WM_LBUTTONUP if is_left else WM_RBUTTONUP
        wparam = MK_LBUTTON if is_left else MK_RBUTTON

        # 1. Gerakkan kursor di antrian pesan jendela target
        user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lparam)
        time.sleep(0.01)

        # 2. Tekan tombol mouse
        user32.PostMessageW(hwnd, down_msg, wparam, lparam)
        if hold_time > 0:
            time.sleep(hold_time)

        # 3. Lepaskan tombol mouse
        user32.PostMessageW(hwnd, up_msg, 0, lparam)

    @staticmethod
    def anti_afk_nudge(hwnd: int) -> None:
        """
        Mengirim rotasi kamera virtual (Right Click + Mouse Move) dan klik background.
        Sangat efektif mereset batas waktu 20 menit idle disconnect Roblox
        100% senyap di latar belakang tanpa mencuri fokus atau mengganggu multitasking.
        """
        if not is_valid_hwnd(hwnd):
            return

        ensure_window_restored(hwnd)
        x, y = get_window_client_center(hwnd)
        lp1 = (y << 16) | (x & 0xFFFF)
        lp2 = (y << 16) | ((x + 12) & 0xFFFF)

        # 1. Gerakkan kursor ke tengah
        user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp1)
        time.sleep(0.01)

        # 2. Sentuhan klik kanan kamera (orbit kamera sejenak)
        user32.PostMessageW(hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lp1)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_MOUSEMOVE, MK_RBUTTON, lp2)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_RBUTTONUP, 0, lp2)

        # 3. Klik kiri virtual singkat di area tengah
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp1)
        time.sleep(0.03)
        user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp1)

    @staticmethod
    def key_down(hwnd: int, vk_code: int) -> None:
        """Mengirim sinyal KeyDown ke jendela target."""
        if not is_valid_hwnd(hwnd):
            return
        ensure_window_restored(hwnd)
        scan_code = user32.MapVirtualKeyW(vk_code, 0)
        lparam = 1 | (scan_code << 16)
        user32.PostMessageW(hwnd, WM_KEYDOWN, vk_code, lparam)

    @staticmethod
    def key_up(hwnd: int, vk_code: int) -> None:
        """Mengirim sinyal KeyUp ke jendela target."""
        if not is_valid_hwnd(hwnd):
            return
        scan_code = user32.MapVirtualKeyW(vk_code, 0)
        lparam = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)
        user32.PostMessageW(hwnd, WM_KEYUP, vk_code, lparam)

    @classmethod
    def key_press(cls, hwnd: int, key_name: str, hold_time: float = 0.05) -> None:
        """Mengirim penekanan tombol lengkap (Down, Char, Up) di background."""
        if not is_valid_hwnd(hwnd):
            return
        vk = cls.get_vk_code(key_name)
        if vk is not None:
            cls.key_down(hwnd, vk)
            if len(key_name) == 1:
                user32.PostMessageW(hwnd, WM_CHAR, ord(key_name), 1)
            if hold_time > 0:
                time.sleep(hold_time)
            cls.key_up(hwnd, vk)

    @staticmethod
    def pulse_to_window(target_hwnd: int, action_fn, pulse_time: float = 0.04) -> None:
        """
        Fokuskan jendela target sekejap (0.04s), jalankan aksi,
        lalu langsung kembalikan fokus ke jendela kerja pengguna semula.
        Sangat ampuh untuk game 3D seperti Roblox yang memblokir background raw input.
        """
        if not is_valid_hwnd(target_hwnd):
            return

        ensure_window_restored(target_hwnd)
        current_active = user32.GetForegroundWindow()
        curr_thread = kernel32.GetCurrentThreadId()
        target_thread = user32.GetWindowThreadProcessId(target_hwnd, None)

        attached = False
        if curr_thread != target_thread:
            attached = bool(user32.AttachThreadInput(curr_thread, target_thread, True))

        try:
            if current_active != target_hwnd:
                SW_RESTORE = 9
                if user32.IsIconic(target_hwnd):
                    user32.ShowWindow(target_hwnd, SW_RESTORE)
                user32.SetForegroundWindow(target_hwnd)
                user32.BringWindowToTop(target_hwnd)
                time.sleep(pulse_time)

            action_fn()
        finally:
            if current_active and current_active != target_hwnd and user32.IsWindow(current_active):
                user32.SetForegroundWindow(current_active)
            if attached:
                user32.AttachThreadInput(curr_thread, target_thread, False)


    @staticmethod
    def get_vk_code(key_name: str) -> Optional[int]:
        """Mengonversi nama tombol string menjadi Virtual Key code Windows."""
        key_lower = key_name.lower().strip()
        if key_lower in VK_CODES:
            return VK_CODES[key_lower]
        if len(key_name) == 1:
            code = user32.VkKeyScanW(ord(key_name))
            if code != -1:
                return code & 0xFF
        return None


class ForegroundController:
    """
    Mengontrol penekanan tombol menggunakan DirectInput ScanCodes (hardware level).
    Menjamin kompabilitas 100% untuk pergerakan 3D di game DirectX/Roblox.
    Dilengkapi thread-safe key tracking dan auto-release failsafe.
    """

    def __init__(self):
        self._active_keys: Set[str] = set()
        self._lock = threading.Lock()

    def press_key(self, key_name: str) -> None:
        """Menahan tombol (KeyDown)."""
        key_lower = key_name.lower().strip()
        with self._lock:
            self._active_keys.add(key_lower)

        if HAS_PYDIRECTINPUT:
            try:
                pydirectinput.keyDown(key_lower)
                return
            except Exception:
                pass

        scancode = SCAN_CODES.get(key_lower)
        if scancode is not None:
            inp = Input(type=INPUT_KEYBOARD)
            inp.ii.ki = KeyBdInput(
                wVk=0,
                wScan=scancode,
                dwFlags=KEYEVENTF_SCANCODE,
                time=0,
                dwExtraInfo=0
            )
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def release_key(self, key_name: str) -> None:
        """Melepaskan tombol (KeyUp)."""
        key_lower = key_name.lower().strip()
        with self._lock:
            self._active_keys.discard(key_lower)

        if HAS_PYDIRECTINPUT:
            try:
                pydirectinput.keyUp(key_lower)
                return
            except Exception:
                pass

        scancode = SCAN_CODES.get(key_lower)
        if scancode is not None:
            inp = Input(type=INPUT_KEYBOARD)
            inp.ii.ki = KeyBdInput(
                wVk=0,
                wScan=scancode,
                dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
                time=0,
                dwExtraInfo=0
            )
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def click(
        self,
        button: MouseButton = MouseButton.LEFT,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> None:
        """
        Melakukan klik mouse di foreground menggunakan SendInput Win32 API.
        Jika x, y diberikan: kursor dipindahkan ke koordinat layar tsb sebelum klik,
        memastikan klik mendarat tepat di dalam jendela game target.
        """
        is_left = (button == MouseButton.LEFT or button == "left")

        # Pindahkan kursor fisik ke koordinat target jika diberikan
        if x is not None and y is not None:
            user32.SetCursorPos(x, y)
            time.sleep(0.03)  # beri waktu pointer OS untuk pindah

        # Coba pydirectinput terlebih dahulu jika tersedia
        if HAS_PYDIRECTINPUT:
            try:
                if x is not None and y is not None:
                    if is_left:
                        pydirectinput.click(x, y)
                    else:
                        pydirectinput.rightClick(x, y)
                else:
                    if is_left:
                        pydirectinput.click()
                    else:
                        pydirectinput.rightClick()
                return
            except Exception:
                pass

        # Fallback: gunakan Win32 SendInput langsung (selalu tersedia)
        down_flag = MOUSEEVENTF_LEFTDOWN if is_left else MOUSEEVENTF_RIGHTDOWN
        up_flag   = MOUSEEVENTF_LEFTUP   if is_left else MOUSEEVENTF_RIGHTUP

        inp_down = Input(type=INPUT_MOUSE)
        inp_down.ii.mi = MouseInput(
            dx=0, dy=0, mouseData=0,
            dwFlags=down_flag,
            time=0, dwExtraInfo=0
        )
        inp_up = Input(type=INPUT_MOUSE)
        inp_up.ii.mi = MouseInput(
            dx=0, dy=0, mouseData=0,
            dwFlags=up_flag,
            time=0, dwExtraInfo=0
        )
        user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
        time.sleep(0.02)
        user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))

    def release_all(self) -> None:
        """Melepaskan seluruh tombol yang sedang aktif ditekan (Failsafe)."""
        with self._lock:
            keys_to_release = list(self._active_keys)
        for key in keys_to_release:
            self.release_key(key)
