import os
import pytest
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from cftable.output import ODSOutputWriter

def test_ods_output_writer(tmp_path):
    results = [
        {'year': 2024, 'Member_age': 40, 'income': 5000000, 'total_assets': 10000000},
        {'year': 2025, 'Member_age': 41, 'income': 5100000, 'total_assets': 11000000},
    ]
    output_path = tmp_path / "test_output.ods"
    
    writer = ODSOutputWriter(results)
    writer.write(str(output_path))
    
    assert os.path.exists(output_path)
    
    # Verify content using odfpy
    doc = load(str(output_path))
    tables = doc.spreadsheet.getElementsByType(Table)
    assert len(tables) == 1
    table = tables[0]
    
    # Check number of rows (header + 2 data rows)
    rows = table.getElementsByType(TableRow)
    # Note: odfpy might have some extra rows depending on how it's saved, but let's check at least 3
    assert len(rows) >= 3
    
    # Check header
    header_cells = rows[0].getElementsByType(TableCell)
    header_texts = [str(c) for c in header_cells]
    # Odfpy's str(cell) might not be just the text, but let's see. 
    # Actually it's better to look at P elements.
    def get_cell_text(cell):
        ps = cell.getElementsByType(P)
        if ps:
            return "".join(str(p) for p in ps) # Simplified
        return ""

    header_texts = [get_cell_text(c) for c in header_cells]
    assert 'year' in header_texts
    assert 'Member_age' in header_texts
    assert 'income' in header_texts
    assert 'total_assets' in header_texts
    
    # Check data row
    data_row = rows[1]
    data_cells = data_row.getElementsByType(TableCell)
    
    # Year: float
    year_cell = data_cells[header_texts.index('year')]
    assert year_cell.getAttribute('valuetype') == 'float'
    assert year_cell.getAttribute('value') == '2024'
    
    # Age: float
    age_cell = data_cells[header_texts.index('Member_age')]
    assert age_cell.getAttribute('valuetype') == 'float'
    assert age_cell.getAttribute('value') == '40'
    
    # Income: currency JPY
    income_cell = data_cells[header_texts.index('income')]
    assert income_cell.getAttribute('valuetype') == 'currency'
    assert income_cell.getAttribute('currency') == 'JPY'
    assert income_cell.getAttribute('value') == '5000000'
    
    # Total Assets: currency JPY
    assets_cell = data_cells[header_texts.index('total_assets')]
    assert assets_cell.getAttribute('valuetype') == 'currency'
    assert assets_cell.getAttribute('currency') == 'JPY'
    assert assets_cell.getAttribute('value') == '10000000'
