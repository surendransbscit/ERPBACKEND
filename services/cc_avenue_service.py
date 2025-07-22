from Crypto.Cipher import AES
import base64
import hashlib

def pad(data):
    pad_len = 16 - len(data) % 16
    return data + (chr(pad_len) * pad_len)

def encrypt(data, working_key):
    key = hashlib.md5(working_key.encode()).digest()
    data = pad(data)
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(data.encode())
    return base64.b64encode(encrypted).decode()

def decrypt(enc_text, working_key):
    key = hashlib.md5(working_key.encode()).digest()
    enc_text = base64.b64decode(enc_text)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(enc_text).decode('utf-8', errors='ignore')
    return decrypted.rstrip('\x10')
