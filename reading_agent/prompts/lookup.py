prompt_parallel_lookup_template = """
The following text is what you remembered from reading an article and a multiple choice question related to it.
You may read 1 to 6 page(s) of the article again to refresh your memory to prepare yourselve for the question.
Please respond with which page(s) you would like to read.
For example, if your only need to read Page 8, respond with \"I want to look up Page [8] to ...\";
if your would like to read Page 7 and 12, respond with \"I want to look up Page [7, 12] to ...\";
if your would like to read Page 2, 3, 7, 15 and 18, respond with \"I want to look up Page [2, 3, 7, 15, 18] to ...\".
if your would like to read Page 3, 4, 5, 12, 13 and 16, respond with \"I want to look up Page [3, 3, 4, 12, 13, 16] to ...\".
DO NOT select more pages if you don't need to.
DO NOT answer the question yet.

Text:
\"\"\"{}\"\"\"

Question:
{}

Take a deep breath and tell me: Which page(s) would you like to read again?
"""


prompt_sequential_lookup_template = """
The following text is what you remember from reading a meeting transcript, followed by a question about the transcript. 
You may read multiple pages of the transcript again to refresh your memory and prepare to answer the question. 
Each page that you re-read can significantly im- prove your chance of answering the question correctly. 
Please specify a SINGLE page you would like to read again or say "STOP". 
To read a page again, respond with “Page $PAGE_NUM”, replacing $PAGE_NUM with the tar- get page number. 
You can only specify a SINGLE page in your response at this time. To stop, simply say “STOP”. 
DO NOT answer the question in your response.

Text:
\"\"\"{}\"\"\"
Pages re-read already (DO NOT ask to read them again): {LIST OF PAGE NUMBERS ALREADY READ}
Question:
{}
Specify a SINGLE page to read again, or say STOP:
"""


prompt_answer_template = """
Read the following article and answer a question.

Article:
\"\"\"{}\"\"\"

Question:
{}

Answer:
"""
