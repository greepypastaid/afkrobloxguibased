import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

def list_all():
    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            len_title = user32.GetWindowTextLengthW(hwnd)
            if len_title > 0:
                t_buf = ctypes.create_unicode_buffer(len_title + 1)
                user32.GetWindowTextW(hwnd, t_buf, len_title + 1)
                c_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, c_buf, 256)
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                print(f"PID={pid.value} | Class='{c_buf.value}' | Title='{t_buf.value}'")
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    user32.EnumWindows(WNDENUMPROC(cb), 0)

if __name__ == "__main__":
    list_all()
