from kallisticore.lib.action import KallistiFunctionCache


def clear_kallisti_functions_cache():
    KallistiFunctionCache().functions = {}
