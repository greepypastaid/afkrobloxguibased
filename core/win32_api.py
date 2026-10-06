"""
core.win32_api
==============
Struktur Win32 ctypes dan fungsi utilitas jendela untuk Windows.
Menangani interaksi level OS seperti enumerasi HWND, pencarian client center, dan fokus jendela.
"""

import ctypes
from ctypes import wintypes
from typing import List, Tuple, Optional
import os

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


def get_window_process_name(hwnd: int) -> str:
    """
    Mengambil nama executable proses yang memiliki jendela (hwnd).
    Digunakan untuk memverifikasi bahwa window adalah Roblox Player asli,
    bukan CustomTkinter atau aplikasi lain dengan class yang sama.
    """
    if not is_valid_hwnd(hwnd):
        return ""
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not h_proc:
        return ""
    try:
        buff = ctypes.create_unicode_buffer(512)
        size = wintypes.DWORD(512)
        # QueryFullProcessImageNameW tersedia di Windows Vista+
        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buff, ctypes.byref(size)):
            return os.path.basename(buff.value).lower()
    finally:
        kernel32.CloseHandle(h_proc)
    return ""


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
    Prioritas utama: cek nama proses (RobloxPlayerBeta.exe)
    Fallback: cek window class (WINDOWSCLIENT) dan judul jendela.
    """
    # Prioritas 1: Cek nama proses - paling akurat, tidak bisa keliru
    if hwnd and is_valid_hwnd(hwnd):
        proc_name = get_window_process_name(hwnd)
        if "robloxplayer" in proc_name or "roblox" in proc_name:
            # Pastikan bukan Roblox Studio
            if "studio" not in proc_name:
                return True

    # Prioritas 2: Cek class Win32
    if hwnd and is_valid_hwnd(hwnd):
        cls_name = get_window_class(hwnd)
        if cls_name == "WINDOWSCLIENT":
            # Verifikasi judul juga untuk menghindari false positive (misal: CustomTkinter)
            t = title.lower().strip()
            if t == "roblox" or t.startswith("roblox") or "roblox player" in t:
                return True

    t = title.lower().strip()
    ignored = [
        "antigravity", "visual studio", "code", "ide", "studio",
        "python", ".py", "afk roblox", "cmd", "powershell", "terminal",
        "afk bot"
    ]
    if any(k in t for k in ignored):
        return False
    return t == "roblox" or t.startswith("roblox") or "roblox player" in t



def find_roblox_hwnd() -> Optional[int]:
    """
    Mencari HWND jendela Roblox Player yang sedang berjalan secara presisi.
    Prioritas 1: Cek proses RobloxPlayerBeta.exe via EnumWindows + process name
    Prioritas 2: Class 'WINDOWSCLIENT' + title 'Roblox'
    Prioritas 3: Filter judul dari daftar get_open_windows()
    """
    best_hwnd: Optional[int] = None

    # 1. Enumerate semua window, cari yang dimiliki oleh proses Roblox Player
    found_hwnds: List[Tuple[int, str]] = []  # (hwnd, proc_name)

    def enum_cb(hwnd: int, lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            proc = get_window_process_name(hwnd)
            if proc and ("robloxplayer" in proc or ("roblox" in proc and "studio" not in proc)):
                found_hwnds.append((hwnd, proc))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    if found_hwnds:
        # Prefer window dengan title tepat 'Roblox'
        for hwnd, _ in found_hwnds:
            buff = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buff, 256)
            if buff.value.strip().lower() == "roblox":
                return hwnd
        # Fallback: ambil yang pertama
        return found_hwnds[0][0]

    # 2. Fallback: FindWindowW via class WINDOWSCLIENT + verifikasi judul
    h_roblox = user32.FindWindowW("WINDOWSCLIENT", None)
    if is_valid_hwnd(h_roblox):
        buff = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(h_roblox, buff, 256)
        title = buff.value.strip()
        if "roblox" in title.lower() and "afk" not in title.lower() and "bot" not in title.lower():
            return h_roblox

    # 3. Fallback: cari via judul jendela
    h_roblox_title = user32.FindWindowW(None, "Roblox")
    if is_valid_hwnd(h_roblox_title) and is_roblox_window("Roblox", h_roblox_title):
        return h_roblox_title

    # 4. Fallback terakhir: scan semua jendela terbuka
    for hwnd, title in get_open_windows():
        if is_roblox_window(title, hwnd):
            return hwnd

    return None



def get_window_client_center(hwnd: int) -> Tuple[int, int]:
    """
    Mengambil titik koordinat tengah area client jendela target (koordinat lokal/client).
    Digunakan untuk penempatan klik PostMessageW di Background Mode.
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


def get_window_screen_center(hwnd: int) -> Tuple[int, int]:
    """
    Mengambil koordinat LAYAR (screen/absolute) dari titik tengah client jendela.
    Berbeda dengan get_window_client_center yang mengembalikan koordinat lokal,
    fungsi ini menggunakan ClientToScreen agar koordinat bisa digunakan oleh
    SetCursorPos / pydirectinput.moveTo() untuk memindahkan kursor fisik.
    Digunakan oleh ForegroundController untuk klik tepat di tengah game target.
    """
    if not is_valid_hwnd(hwnd):
        return (400, 300)

    # Ambil ukuran area client
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        return (400, 300)

    client_cx = max(50, (rect.right - rect.left) // 2)
    client_cy = max(50, (rect.bottom - rect.top) // 2)

    # Konversi koordinat client → koordinat layar
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    pt = POINT(client_cx, client_cy)
    if user32.ClientToScreen(hwnd, ctypes.byref(pt)):
        return (pt.x, pt.y)

    # Fallback: GetWindowRect jika ClientToScreen gagal
    win_rect = wintypes.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(win_rect)):
        cx = (win_rect.left + win_rect.right) // 2
        cy = (win_rect.top + win_rect.bottom) // 2
        return (cx, cy)

    return (400, 300)


def focus_window(hwnd: int) -> bool:
    """Membawa jendela target ke latar depan (foreground)."""
    if not is_valid_hwnd(hwnd):
        return False
    ensure_window_restored(hwnd)
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    return bool(user32.SetForegroundWindow(hwnd))

