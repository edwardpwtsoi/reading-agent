from typing import List, Optional

from pydantic import BaseModel


class Paragraph(BaseModel):
    content: str


class TableCell(BaseModel):
    column_id: int
    row_id: int
    content: str


class Table(BaseModel):
    num_of_columns: int
    num_of_rows: int
    cells: List[TableCell]
    caption: Optional[str] = None

    def to_csv(self) -> List[List[str]]:
        # Initialize an empty list of lists to store the table data
        data = [['' for _ in range(self.num_of_columns)] for _ in range(self.num_of_rows)]
        # Fill the data list with the cell values from the table
        for cell in self.cells:
            row_index = cell.row.id
            column_index = cell.column.id
            content = cell.content
            data[row_index][column_index] = content
        return data

    def to_csv_str(self) -> str:
        data = self.to_csv()
        return '\n'.join(', '.join(row) for row in data)
