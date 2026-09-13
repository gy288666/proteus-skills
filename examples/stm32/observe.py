"""Passive observation only: no input, window movement or application mutation."""
import ctypes as C
from ctypes import wintypes as W
from PIL import ImageGrab

u = C.WinDLL('user32', use_last_error=True)
CALLBACK = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u.GetWindowThreadProcessId.argtypes = (W.HWND, C.POINTER(W.DWORD))
u.GetWindowTextW.argtypes = (W.HWND, W.LPWSTR, C.c_int)
u.GetWindowTextLengthW.argtypes = (W.HWND,)
u.GetClassNameW.argtypes = (W.HWND, W.LPWSTR, C.c_int)
u.IsWindowVisible.argtypes = (W.HWND,)
u.GetMenu.argtypes = (W.HWND,)
u.GetMenu.restype = W.HMENU
u.GetWindowRect.argtypes = (W.HWND, C.POINTER(W.RECT))
u.GetMenuItemCount.argtypes = (W.HMENU,)
u.GetSubMenu.argtypes = (W.HMENU, C.c_int)
u.GetSubMenu.restype = W.HMENU
u.GetMenuStringW.argtypes = (W.HMENU, W.UINT, W.LPWSTR, C.c_int, W.UINT)

def windows(pid=None, prefix=None):
    rows = []
    @CALLBACK
    def visit(h, _):
        p = W.DWORD()
        u.GetWindowThreadProcessId(h, C.byref(p))
        title = C.create_unicode_buffer(u.GetWindowTextLengthW(h) + 1)
        u.GetWindowTextW(h, title, len(title))
        if u.IsWindowVisible(h) and ((pid is not None and p.value == pid) or
                (prefix and title.value.startswith(prefix + ' - Proteus'))):
            rect = W.RECT()
            u.GetWindowRect(h, C.byref(rect))
            cls = C.create_unicode_buffer(256)
            u.GetClassNameW(h, cls, len(cls))
            rows.append(dict(hwnd=h, pid=p.value, title=title.value,
                             cls=cls.value,
                             menu=u.GetMenu(h), rect=(rect.left, rect.top, rect.right, rect.bottom)))
        return True
    u.EnumWindows(visit, 0)
    return rows

def menu_paths(menu, prefix=''):
    rows = []
    for i in range(u.GetMenuItemCount(menu)):
        buf = C.create_unicode_buffer(512)
        u.GetMenuStringW(menu, i, buf, len(buf), 0x400)
        label = buf.value.replace('&', '').split('\t')[0].strip()
        if not label:
            continue
        path = prefix + '/' + label if prefix else label
        sub = u.GetSubMenu(menu, i)
        rows.extend(menu_paths(sub, path) if sub else [path])
    return rows

def capture(pid=None, prefix=None):
    rows = windows(pid, prefix)
    main = next((r for r in rows if r['menu'] and ' - Proteus' in r['title']), None)
    if not main:
        return None, []
    # Capture just this process, even if another app is covering it.
    im = ImageGrab.grab(window=main['hwnd'])
    dialogs = [r for r in windows(pid=main['pid']) if r['hwnd'] != main['hwnd'] and r['title']]
    for row in reversed(dialogs):
        # The recording targets the schematic window and native modal forms.
        # Separate debugger tool windows are logged, not pasted over the canvas.
        if row['cls'] != '#32770':
            continue
        try:
            overlay = ImageGrab.grab(window=row['hwnd'])
            # PrintWindow may exclude the outer border; center within the owned
            # window's observed rectangle rather than inventing dialog contents.
            x = row['rect'][0] - main['rect'][0]
            y = row['rect'][1] - main['rect'][1]
            im.paste(overlay, (max(0, x), max(0, y)))
        except OSError:
            pass
    return im, [r['title'] for r in dialogs]

if __name__ == '__main__':
    import json, sys
    rows = windows(pid=int(sys.argv[1]))
    print(json.dumps([dict(title=r['title'], menus=menu_paths(r['menu']) if r['menu'] else []) for r in rows], indent=2))
