import hashlib


def get_sha256_hash(text: str) -> str:
    byte_text = text.encode("utf-8")
    sha256_hash = hashlib.sha256()
    sha256_hash.update(byte_text)
    return sha256_hash.hexdigest()
