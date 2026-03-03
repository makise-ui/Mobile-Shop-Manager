"""
Toast notification helper for the Mobile Shop Manager app.
Provides a simple API to show non-blocking toast notifications.
"""
from ttkbootstrap.toast import ToastNotification


def show_toast(title, message, kind="info", duration=3000):
    """
    Show a non-blocking toast notification.
    
    Args:
        title: Toast title text.
        message: Toast body message.
        kind: One of 'success', 'warning', 'danger', 'info'.
        duration: Auto-dismiss time in milliseconds (default 3000ms).
    """
    toast = ToastNotification(
        title=title,
        message=message,
        duration=duration,
        bootstyle=kind
    )
    toast.show_toast()
