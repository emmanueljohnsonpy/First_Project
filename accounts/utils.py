import random
import string

def generate_referral_code(length=8):
    """Generate a random referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
