import string

chars = string.ascii_letters + string.digits

def encode(num: int) -> str:
    base = len(chars)
    res = []

    while num > 0:
        res.append(chars[num % base])
        num //= base

    return ''.join(res[::-1]) or "0"