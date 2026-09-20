"""
core.win32_api
==============
Struktur Win32 ctypes dan fungsi utilitas jendela untuk Windows.
Menangani interaksi level OS seperti enumerasi HWND, pencarian client center, dan fokus jendela.
"""

import ctypes
from ctypes import wintypes
from typing import List, Tuple, Optional

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ==========================================
# CTYPES STRUCTURES
# ==========================================
class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    ]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    ]

class Input_I(ctypes.Union):
    _fields_ = [('ki', KeyBdInput), ('mi', MouseInput), ('hi', HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD), ('ii', Input_I)]


# ==========================================
# WINDOW UTILITY FUNCTIONS
# ==========================================
def is_valid_hwnd(hwnd: Optional[int]) -> bool:
    """Memeriksa apakah handle jendela valid dan masih aktif."""
    return bool(hwnd and user32.IsWindow(hwnd))


def ensure_window_restored(hwnd: int) -> None:
    """
    Memastikan jendela tidak dalam keadaan minimize ke taskbar.
    Jika minimized, pulihkan tanpa mengaktifkannya secara agresif (SW_SHOWNOACTIVATE = 4).
    """
    if is_valid_hwnd(hwnd) and user32.IsIconic(hwnd):
        SW_SHOWNOACTIVATE = 4
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)


def get_window_class(hwnd: int) -> str:
    """Mengambil nama window class Win32."""
    if not is_valid_hwnd(hwnd):
        return ""
    buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buff, 256)
    return buff.value.strip()


def get_open_windows() -> List[Tuple[int, str]]:
    """
    Mengembalikan daftar tuple (hwnd, title) untuk semua jendela aktif yang terlihat.
    Mengabaikan jendela sistem kosong dan jendela IDE/editor.
    """
    windows: List[Tuple[int, str]] = []
    ignored_titles = {
        "Program Manager",
        "Settings",
        "Microsoft Text Input Application",
        "Windows Input Experience"
    }

    def enum_callback(hwnd: int, lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                if title and title not in ignored_titles:
                    windows.append((hwnd, title))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    c_cb = WNDENUMPROC(enum_callback)
    user32.EnumWindows(c_cb, 0)

    # Fallback untuk lingkungan desktop terpisah jika daftar kosong
    if not windows:
        h_desk = user32.OpenDesktopW("Default", 0, False, 0x0100 | 0x0001 | 0x0002)
        if h_desk:
            try:
                user32.EnumDesktopWindows(h_desk, c_cb, 0)
            finally:
                user32.CloseDesktop(h_desk)

    return windows


def is_roblox_window(title: str, hwnd: Optional[int] = None) -> bool:
    """
    Mengecek apakah jendela adalah game Roblox Player asli.
    Memeriksa nama class Win32 (WINDOWSCLIENT) dan memfilter editor/IDE.
    """
    if hwnd and is_valid_hwnd(hwnd):
        cls_name = get_window_class(hwnd)
        if cls_name == "WINDOWSCLIENT":
            return True

    t = title.lower().strip()
    ignored = [
        "antigravity", "visual studio", "code", "ide", "studio",
        "python", ".py", "afk roblox", "cmd", "powershell", "terminal"
    ]
    if any(k in t for k in ignored):
        return False
    return t == "roblox" or t.startswith("roblox") or "roblox player" in t



def find_roblox_hwnd() -> Optional[int]:
    """
    Mencari HWND jendela Roblox Player yang sedang berjalan secara presisi.
    Prioritas 1: Class 'WINDOWSCLIENT' (class resmi Roblox Player)
    Prioritas 2: Jendela dengan judul 'Roblox'
    Prioritas 3: Filter jendela dari daftar get_open_windows()
    """
    # 1. Cek langsung via nama Class resmi Roblox
    h_roblox = user32.FindWindowW("WINDOWSCLIENT", None)
    if is_valid_hwnd(h_roblox):
        return h_roblox

    # 2. Cek via judul jendela "Roblox"
    h_roblox_title = user32.FindWindowW(None, "Roblox")
    if is_valid_hwnd(h_roblox_title) and is_roblox_window("Roblox", h_roblox_title):
        return h_roblox_title

    # 3. Fallback pencarian daftar jendela terbuka
    for hwnd, title in get_open_windows():
        if is_roblox_window(title, hwnd):
            return hwnd

    return None



def get_window_client_center(hwnd: int) -> Tuple[int, int]:
    """
    Mengambil titik koordinat tengah area client jendela target.
    Digunakan untuk penempatan klik mouse yang akurat.
    """
    if not is_valid_hwnd(hwnd):
        return (200, 200)

    rect = wintypes.RECT()
    success = user32.GetClientRect(hwnd, ctypes.byref(rect))
    if success:
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return max(50, width // 2), max(50, height // 2)
    return (200, 200)


def focus_window(hwnd: int) -> bool:
    """Membawa jendela target ke latar depan (foreground)."""
    if not is_valid_hwnd(hwnd):
        return False
    ensure_window_restored(hwnd)
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))

