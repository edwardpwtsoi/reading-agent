import re
from typing import List


def count_words(text):
    """Simple word counting."""
    return len(text.split())


def encode_paragraphs(raw: str):
    return raw.split("\n\n")


def decode_paragraphs(paragraphs: List[str]):
    return "\n\n".join(paragraphs)


def encode_gists(raw: str):
    return [g.split(":", 1)[1].strip() for g in raw.split("\n\n")]


def decode_gists(gists: List[str]) -> str:
    return "\n\n".join([f"{i}: {c}" for i, c in enumerate(gists)])


def encode_pages(raw: str):
    return [eval(p.split(":", 1)[1].strip()) for p in raw.split("\n\n")]


def decode_pages(pages: List[List[str]]) -> str:
    return "\n\n".join([f"{i}: {c}" for i, c in enumerate(pages)])


def replace_consecutive_newlines(input_string):
    return re.sub(r'\n{2,}', '\n', input_string)
