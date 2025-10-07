import os, base64, hmac, hashlib
KEY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "secret.key"))
def _key():
    try:
        with open(KEY_FILE,"rb") as f: return f.read()
    except Exception:
        k=os.urandom(32)
        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
        with open(KEY_FILE,"wb") as f: f.write(k)
        return k
def seal(plaintext: str) -> str:
    k=_key(); data=plaintext.encode("utf-8")
    stream = bytearray((data[i] ^ k[i % len(k)]) for i in range(len(data)))
    mac = hmac.new(k, stream, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac + stream).decode("ascii")
def open_sealed(token: str) -> str:
    k=_key()
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    mac, stream = raw[:32], bytearray(raw[32:])
    if not hmac.compare_digest(mac, hmac.new(k, stream, hashlib.sha256).digest()):
        raise ValueError("bad mac")
    data = bytearray((stream[i] ^ k[i % len(k)]) for i in range(len(stream)))
    return data.decode("utf-8")
