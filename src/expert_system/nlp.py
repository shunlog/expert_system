#!/bin/env python3

def sentence_to_question(sentence):
    '''Converts a statement into a question. The statement must have one of these 4 forms:
    1. it is ...
    2. it has ...
    3. it <verb that ends with "s"> ...
    4. it doesn't ...
    '''
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
