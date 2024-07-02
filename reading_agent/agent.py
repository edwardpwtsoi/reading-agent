import logging
from typing import List

from reading_agent.backends.base import BackendBase
from reading_agent.prompts.lookup import prompt_parallel_lookup_template, prompt_answer_template
from reading_agent.prompts.pagination import prompt_pagination_template, parse_pause_point
from reading_agent.prompts.shorten import prompt_shorten_template
from reading_agent.utils import count_words, replace_consecutive_newlines

logger = logging.getLogger(__name__)


class Agent:
    @staticmethod
    def pagination(
        paragraphs: List[str],
        backend: BackendBase,
        word_limit=600,
        start_threshold=280,
        verbose=True,
        allow_fallback_to_last=True
    ) -> List[List[str]]:

        i = 0
        total_token_used = 0
        pages = []
        while i < len(paragraphs):
            preceding = "" if i == 0 else "...\n" + '\n'.join(pages[-1])
            passage = [paragraphs[i]]
            wcount = count_words(paragraphs[i])
            j = i + 1
            while wcount < word_limit and j < len(paragraphs):
                wcount += count_words(paragraphs[j])
                if wcount >= start_threshold:
                    passage.append(f"<{j}>")
                passage.append(paragraphs[j])
                j += 1
            passage.append(f"<{j}>")
            end_tag = "" if j == len(paragraphs) else paragraphs[j] + "\n..."

            pause_point = None
            if wcount < 350:
                pause_point = len(paragraphs)
            else:
                prompt = prompt_pagination_template.format(preceding, '\n'.join(passage), end_tag)
                token_usage, response = backend.query_model(prompt=prompt)
                total_token_used += token_usage
                response = response.strip()
                pause_point = parse_pause_point(response)
                if pause_point and (pause_point <= i or pause_point > j):
                    logger.info(f"prompt:\n{prompt},\nresponse:\n{response}\n")
                    logger.info(f"i:{i} j:{j} pause_point:{pause_point}")
                    pause_point = None
                if pause_point is None:
                    if allow_fallback_to_last:
                        pause_point = j
                    else:
                        raise ValueError(f"prompt:\n{prompt},\nresponse:\n{response}\n")

            page = paragraphs[i:pause_point]
            pages.append(page)
            if verbose:
                logger.info(f"[Pagination] Paragraph {i}-{pause_point - 1} {page}")
            i = pause_point
        logger.info(f"[Pagination] Done with {len(pages)} pages, token usage: {total_token_used}")
        return pages

    @staticmethod
    def gisting(pages: List[List[str]], backend: BackendBase, verbose=True):
        article = '\n'.join([t for p in pages for t in p])
        word_count = count_words(article)
        logger.info(f"[Gisting] Document Word Count: {word_count}")
        shortened_pages = []
        total_token_used = 0
        for i, page in enumerate(pages):
            prompt = prompt_shorten_template.format('\n'.join(page))
            token_usage, response = backend.query_model(prompt)
            total_token_used += token_usage
            shortened_text = replace_consecutive_newlines(response.strip())
            shortened_pages.append(shortened_text)
            if verbose:
                logger.info(f"[Gisting] page {i}: {shortened_text}")
        shortened_article = '\n'.join(shortened_pages)
        gist_word_count = count_words(shortened_article)
        if verbose:
            logger.info(f"[Gisting] Shortened article:\n {shortened_article}")
        if verbose:
            logger.info(
                f"[Gisting] compression rate {round(100.0 - gist_word_count / word_count * 100, 2)}% ({gist_word_count}/{word_count}), "
                f"token usage: {total_token_used}"
            )
        return shortened_pages

    @staticmethod
    def parallel_lookup(gists, pages, question, backend, verbose=True):
        shortened_article = '\n'.join(gists)
        prompt_lookup = prompt_parallel_lookup_template.format(shortened_article, question)
        page_ids = []
        total_token_used = 0
        token_usage, response = backend.query_model(prompt=prompt_lookup)
        total_token_used += token_usage
        response = response.strip()
        try:
            start = response.index('[')
        except ValueError:
            start = len(response)
        try:
            end = response.index(']')
        except ValueError:
            end = 0
        if start < end:
            page_ids_str = response[start + 1:end].split(',')
            page_ids = []
            for p in page_ids_str:
                if p.strip().isnumeric():
                    page_id = int(p)
                    if page_id < 0 or page_id >= len(pages):
                        logger.info(f"[Look Up] Skip invalid page number: {page_id}")
                    else:
                        page_ids.append(page_id)

        if verbose:
            logger.info("[Look Up] Model chose to look up page {}".format(page_ids))

        # Memory expansion after look-up, replacing the target shortened page with the original page
        expanded_shortened_pages = gists[:]
        if len(page_ids) > 0:
            for page_id in page_ids:
                expanded_shortened_pages[page_id] = '\n'.join(pages[page_id])

        expanded_shortened_article = '\n'.join(expanded_shortened_pages)
        if verbose:
            logger.info(f"[Look Up] Expanded shortened article:\n {expanded_shortened_article}")
        prompt_answer = prompt_answer_template.format(expanded_shortened_article, question)

        token_usage, response = backend.query_model(prompt=prompt_answer)
        total_token_used += total_token_used
        response = response.strip()
        logger.info(f"[Look Up] Token usage: {total_token_used}")
        return response
