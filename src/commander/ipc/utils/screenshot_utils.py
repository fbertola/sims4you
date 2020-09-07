from PIL import ImageGrab
import win32gui
import win32com.client
import time


def take_window_screenshot(window_name):
    toplist, winlist = [], []

    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_cb, toplist)

    window_to_screenshot = list(((hwnd, title) for hwnd, title in winlist if window_name in title))

    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys('%')
    window_to_screenshot = window_to_screenshot[0]
    hwnd = window_to_screenshot[0]
    win32gui.SetForegroundWindow(hwnd)
    bbox = win32gui.GetWindowRect(hwnd)
    time.sleep(1)
    img = ImageGrab.grab(bbox)
    img.show()
