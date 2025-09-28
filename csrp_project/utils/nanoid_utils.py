# utils/nanoid_utils.py
from nanoid import generate

def generate_nano_id(size=21):
    """Generate a NanoID with custom size"""
    return generate(size=size)

def generate_custom_nano_id(alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', size=10):
    """Generate a NanoID with custom alphabet"""
    return generate(alphabet=alphabet, size=size)
