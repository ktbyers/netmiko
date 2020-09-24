import difflib


def guess(word, possibilities, count=3, cutoff=0.8):
    return difflib.get_close_matches(word, possibilities, n=count, cutoff=cutoff)