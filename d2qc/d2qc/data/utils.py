import hashlib
import numbers

def shash(var):
    """
        Simple hash implementation for percistently hashing across sessions.
        Python hash - function hashes same string to different value in
        different session. Numbers are simply hashed to them selves as a string.
        Strings are hashed using md5, converted to a long int, and converted
        back to a string.
    """
    if (
            isinstance(var, numbers.Integral)
            or isinstance(var, float)
    ):
        return str(var)
    var = str(var).encode('utf-8', 'ignore')
    return str(int(hashlib.md5(var).hexdigest(), 16)%pow(10,15))
