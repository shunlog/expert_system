#!/bin/env python3

def sentence_to_question(sentence):
    words = sentence.split()

    if len(words) < 2:
        return sentence  # Not a valid sentence for conversion

    subject = "it"
    verb = words[0]
    rest = " ".join(words[1:])

    if verb == "is":
        return f"Is {subject} {rest}?"
    elif verb == "has":
        return f"Does {subject} have {rest}?"
    elif verb == "doesn't":
        return f"Does {subject} not {rest}?"
    elif verb.endswith("s"):
        return f"Does {subject} {verb[:-1]} {rest}?"
    return sentence
