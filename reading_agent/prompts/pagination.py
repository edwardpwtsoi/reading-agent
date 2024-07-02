prompt_pagination_template = """
You are given a passage that is taken from a larger text (article, book, ...) and some numbered labels between the paragraphs in the passage.
Numbered label are in angeled brackets. For example, if the label number is 19, it shows as <19> in text.
Please choose one label that it is natural to break reading.
Such point can be scene transition, end of a dialogue, end of an argument, narrative transition, etc.
Please answer the break point label and explain.
For example, if <57> is a good point to break, answer with \"Break point: <57>\n Because ...\"

Passage:

{0}
{1}
{2}

"""


def parse_pause_point(text):
    text = text.strip("Break point: ")
    if text[0] != '<':
        return None
    for i, c in enumerate(text):
        if c == '>':
            if text[1:i].isnumeric():
                return int(text[1:i])
            else:
                return None
    return None
