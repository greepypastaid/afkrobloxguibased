import ctypes
from ctypes import wintypes
import subprocess

user32 = ctypes.windll.user32

def find_roblox():
    out = subprocess.check_output(['powershell', '-NoProfile', '-Command', '(Get-Process -Name RobloxPlayerBeta -ErrorAction SilentlyContinue).Id']).decode().strip()
    if not out:
        print("No Roblox process found.")
        return
    pids = [int(p) for p in out.split() if p.isdigit()]
    print("Roblox PIDs:", pids)

    def enum_cb(hwnd, extra):
        lpdw_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_pid))
        if lpdw_pid.value in pids:
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            class_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buff, 256)
            is_vis = user32.IsWindowVisible(hwnd)
            print(f"FOUND: HWND={hwnd}, Title='{buff.value}', Class='{class_buff.value}', Visible={is_vis}")
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

if __name__ == "__main__":
    find_roblox()
