import random
import string
import re
import json


def generate_chart_session():
    return f"cs_{get_random_alpha(10)}"


def generate_quote_session():
    return  f"qs_{get_random_alpha(10)}"


def get_random_alpha(length):
    """Generate a random string"""
    str = string.ascii_letters
    return ''.join(random.choice(str) for i in range(length))


def strip(text):
    no_data_reg = re.match('~m~\\d+~m~~h~\\d+', text, re.MULTILINE)
    if not no_data_reg:
        data_reg = re.split('~m~\\d+~m~', text)
        return [json.loads(t) for t in data_reg if t]
    return []


def unstrip(text):
    return f"~m~{len(text) - 8}~m~{json.dumps(text)}"
