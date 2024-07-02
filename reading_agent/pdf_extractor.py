"""
This code sample shows Prebuilt Read operations with the Azure Form Recognizer client library. 
The async versions of the samples require Python 3.6 or later.

To learn more, please visit the documentation - Quickstart: Document Intelligence (formerly Form Recognizer) SDKs
https://learn.microsoft.com/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api?pivots=programming-language-python
"""
import binascii
import os
import time
from typing import List
from functools import reduce

from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from reading_agent.utils import replace_consecutive_newlines

"""
Remember to remove the key from your code when you're done, and never post it publicly. For production, use
secure methods to store and access your credentials. For more information, see 
https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-security?tabs=command-line%2Ccsharp#environment-variables-and-application-configuration
"""


class AzureDocumentIntelligenceExtractor:
    def __init__(self):
        super().__init__()
        self.document_intelligence_client = DocumentIntelligenceClient(
            endpoint=os.environ["AZURE_FORM_RECOGNIZER_API_ENDPOINT"],
            credential=AzureKeyCredential(os.environ["AZURE_FORM_RECOGNIZER_API_KEY"])
        )

    def __call__(self, pdf_bytes) -> List[str]:
        paragraphs = []
        result = self.layout(pdf_bytes)
        table_elem_indices = [set(indices) for indices in self._extract_table_elements_indices(result.tables)]
        table_elem_indices_flatten = reduce(set().union, table_elem_indices) if table_elem_indices else []
        figure_elem_indices = [set(indices) for indices in self._extract_figure_elements_indices(result.figures)]
        figure_elem_indices_flatten = reduce(set().union, figure_elem_indices) if figure_elem_indices else []
        i = 0
        while i < len(result.paragraphs):
            if i in table_elem_indices_flatten:
                # check which table does it belong to
                for table_idx, table_elem_indices_per_table in enumerate(table_elem_indices):
                    if i in table_elem_indices_per_table:
                        paragraphs.append(self._dump_table_into_csv(result.tables[table_idx]))
                        i += len(table_elem_indices_per_table)
            elif i in figure_elem_indices_flatten:
                i += 1
            else:
                paragraphs.append(result.paragraphs[i].content)
                i += 1
        return [replace_consecutive_newlines(x) for x in paragraphs]

    @staticmethod
    def _extract_table_elements_indices(instances) -> List[List[int]]:
        if instances:
            return [[int(e.rsplit("/", 1)[-1]) for cell in instance["cells"] if cell.elements
                    for e in cell.elements] for instance in instances]
        else:
            return []

    @staticmethod
    def _extract_figure_elements_indices(instances) -> List[List[int]]:
        if instances:
            return [[int(e.rsplit("/", 1)[-1]) for e in instance.elements]
                    for instance in instances if instance.elements]
        else:
            return []

    def read(self, pdf_bytes) -> AnalyzeResult:
        poller = self.document_intelligence_client.begin_analyze_document(
            "prebuilt-read",
            json={"base64Source": binascii.b2a_base64(pdf_bytes).decode()}
        )
        delay = 30
        max_delay = 3840
        while not poller.done() and delay < max_delay:
            time.sleep(delay)
            delay *= 2
        result = poller.result()
        return result

    def layout(self, pdf_bytes) -> AnalyzeResult:
        poller = self.document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            json={"base64Source": binascii.b2a_base64(pdf_bytes).decode()}
        )
        delay = 30
        max_delay = 3840
        while not poller.done() and delay < max_delay:
            time.sleep(delay)
            delay *= 2
        result = poller.result()
        return result

    @staticmethod
    def _table_to_csv(table) -> List[List[str]]:
        # Initialize an empty list of lists to store the table data
        data = [['' for _ in range(table['columnCount'])] for _ in range(table['rowCount'])]
        # Fill the data list with the cell values from the table
        for cell in table['cells']:
            row_index = cell['rowIndex']
            column_index = cell['columnIndex']
            content = cell['content']
            data[row_index][column_index] = content
        return data

    def _dump_table_into_csv(self, table) -> str:
        data = self._table_to_csv(table)
        return '\n'.join(', '.join(row) for row in data)
