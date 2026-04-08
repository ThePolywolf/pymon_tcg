import hashlib

def get_hash(*args):
    """
    Hashes arguments into a 32bit integer value
    """
    raw = "".join([str(arg) for arg in args])
    h = hashlib.md5(raw.encode()).digest()
    return int.from_bytes(h, 'big') & ((1 << 32) - 1)