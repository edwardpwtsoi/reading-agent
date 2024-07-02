import argparse
import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import gradio as gr
from gradio_pdf import PDF
from dotenv import load_dotenv

from reading_agent.agent import Agent
from reading_agent.pdf_extractor import AzureDocumentIntelligenceExtractor
from reading_agent.utils import encode_gists, encode_pages, decode_gists, decode_pages, decode_paragraphs, encode_paragraphs

load_dotenv()


def init_logger(level: str):
    level = logging.getLevelName(level)

    # create logger
    logger = logging.getLogger('readagent')
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


def exception_handling(logger=None):
    def exception_handling_wrapping(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                raise gr.Error(f"{exc}") from None
        return wrapper
    return exception_handling_wrapping


def get_backend(backend_name):
    if backend_name == "gpt":
        from readagent.backends.chatgpt import GPTBackend
        return GPTBackend()
    elif backend_name == "gemini":
        from readagent.backends.gemini import GeminiBackend
        return GeminiBackend()
    elif backend_name == "haiku":
        from readagent.backends.bedrock import Claude3Backend
        return Claude3Backend()
    else:
        raise ValueError("Unknown backend")


def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logging_level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="DEBUG")
    parser.add_argument("--server_name", default=None, type=str)
    parser.add_argument("--server_port", default=None, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_cli_args()
    init_logger(cli_args.logging_level)
    default_logger = logging.getLogger("reading_agent")
    agent = Agent()
    pdf_extractor = AzureDocumentIntelligenceExtractor()

    paragraphs_memory_temporary_file = NamedTemporaryFile(delete=False, prefix="paragraphs_", suffix=".json")
    paragraphs_memory_temporary_filename = paragraphs_memory_temporary_file.name
    gists_memory_temporary_file = NamedTemporaryFile(delete=False, prefix="gists_", suffix=".json")
    gists_memory_temporary_filename = gists_memory_temporary_file.name
    pages_memory_temporary_file = NamedTemporaryFile(delete=False, prefix="pages_", suffix=".json")
    pages_memory_temporary_filename = pages_memory_temporary_file.name

    def chat(message, history, gists_raw, pages_raw, backend_name):
        gists = encode_gists(gists_raw)
        pages = encode_pages(pages_raw)
        backend = get_backend(backend_name)
        response = agent.parallel_lookup(gists, pages, message, backend)
        return response

    with gr.Blocks(fill_height=True) as demo:
        # layout
        gr.Markdown("# Document")
        pdf_file = PDF(label="Document")
        submit = gr.Button("Submit", interactive=False)
        paragraph_view = gr.Textbox(label="Paragraphs", interactive=True, show_copy_button=True)
        with gr.Row():
            paragraphs_upload = gr.UploadButton("Upload paragraphs.json")
            paragraphs_download = gr.DownloadButton("Download paragraphs.json")
        backend_dropdown = gr.Dropdown(choices=["gpt", "gemini", "haiku"], label="Backend")
        read = gr.Button("Read", interactive=False)
        with gr.Row():
            gists_view = gr.Textbox(label="Gists", interactive=True, show_copy_button=True)
            pages_view = gr.Textbox(label="Pages", interactive=True, show_copy_button=True)
        with gr.Row():
            gists_upload = gr.UploadButton("Upload gists.json")
            gists_download = gr.DownloadButton("Download gists.json")
            pages_upload = gr.UploadButton("Upload pages.json")
            pages_download = gr.DownloadButton("Download pages.json")
        gr.ChatInterface(fn=chat, title="Read Agent", additional_inputs=[gists_view, pages_view, backend_dropdown],
                         examples=[["What's the major contribution of this paper?"]])

        # callbacks
        def on_pdf_upload(pdf_file):
            if pdf_file is not None:
                return gr.Button("Submit", interactive=True)
            else:
                return gr.Button("Submit", interactive=False)

        @exception_handling(logger=default_logger)
        def submit_pdf(pdf_file, paragraphs_raw):
            if pdf_file is not None:
                pdf_bytes = Path(pdf_file).read_bytes()
                paragraphs = pdf_extractor(pdf_bytes)
                return decode_paragraphs(paragraphs)
            else:
                return paragraphs_raw

        def upload_paragraphs(filepath):
            with open(filepath, "r") as f:
                paragraphs_dict = json.load(f)
            paragraphs = paragraphs_dict["paragraphs"]
            return decode_paragraphs(paragraphs)

        def download_paragraphs(paragraphs_raw):
            with open(paragraphs_memory_temporary_filename, "w") as f:
                json.dump({"paragraphs": encode_paragraphs(paragraphs_raw)}, f)
            return paragraphs_memory_temporary_filename


        @exception_handling(logger=default_logger)
        def read_paragraphs(paragraphs_raw, backend_name, gists_raw, pages_raw):
            if paragraphs_raw is not None and backend_name is not None:
                backend = get_backend(backend_name)
                paragraphs = encode_paragraphs(paragraphs_raw)
                pages = agent.pagination(paragraphs, backend)
                gists = agent.gisting(pages, backend)
                return decode_gists(gists), decode_pages(pages)
            else:
                return gists_raw, pages_raw

        def on_backend_dropdown_change(backend_name):
            if backend_name is not None:
                return gr.Button("Read", interactive=True)
            else:
                return gr.Button("Read", interactive=False)

        def upload_gists(filepath):
            with open(filepath, "r") as f:
                gists_dict = json.load(f)
            gists = gists_dict["gists"]
            return decode_gists(gists)

        def download_gists(gists_raw):
            with open(gists_memory_temporary_filename, "w") as f:
                json.dump({"gists": encode_gists(gists_raw)}, f)
            return gists_memory_temporary_filename

        def upload_pages(filepath):
            with open(filepath, "r") as f:
                pages_dict = json.load(f)
            pages = pages_dict["pages"]
            return decode_pages(pages)

        def download_pages(pages_raw):
            with open(pages_memory_temporary_filename, "w") as f:
                json.dump({"pages": encode_pages(pages_raw)}, f)
            return pages_memory_temporary_filename

        # interaction
        pdf_file.change(on_pdf_upload, inputs=pdf_file,  outputs=submit)
        submit.click(submit_pdf, inputs=[pdf_file, paragraph_view], outputs=paragraph_view)
        paragraphs_upload.upload(upload_paragraphs, inputs=paragraphs_upload, outputs=paragraph_view)
        paragraphs_download.click(download_paragraphs,  inputs=paragraph_view, outputs=paragraphs_download)
        backend_dropdown.change(on_backend_dropdown_change, inputs=backend_dropdown, outputs=read)
        read.click(read_paragraphs, inputs=[paragraph_view, backend_dropdown, gists_view, pages_view],
                   outputs=[gists_view, pages_view])
        gists_upload.upload(upload_gists, inputs=gists_upload, outputs=gists_view)
        gists_download.click(download_gists,  inputs=gists_view, outputs=gists_download)
        pages_upload.upload(upload_pages, inputs=pages_upload, outputs=pages_view)
        pages_download.click(download_pages,  inputs=pages_view, outputs=pages_download)
    demo.launch(server_name=cli_args.server_name, server_port=cli_args.server_port,
                auth=None if os.environ.get("DEBUG", 0)
                else (os.environ["GRADIO_READAGENT_DEFAULT_USERNAME"], os.environ["GRADIO_READAGENT_DEFAULT_PASSWORD"]))
