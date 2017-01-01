import os
import platform


def get_free_space(dir_name):
    """Get free space in bytes for the path provided

    :param dir_name:
    :return:
    """
    if platform.system() == 'Windows':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(dir_name), None, None, ctypes.pointer(free_bytes)
        )
        return free_bytes.value
    else:
        st = os.statvfs(dir_name)
        return st.f_bavail * st.f_frsize
