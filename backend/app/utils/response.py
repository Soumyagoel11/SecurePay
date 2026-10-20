"""Standard API response helpers."""


def success(message="Success", data=None, status=200):
    return (
        {"success": True, "message": message, "data": data if data is not None else {}},
        status,
    )


def error(message="Error", status=400, data=None):
    return (
        {"success": False, "message": message, "data": data if data is not None else {}},
        status,
    )
