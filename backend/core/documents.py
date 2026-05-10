"""
Nexus AI - Document Creator (Lazy Loading)
Crea documentos Word, Excel y PowerPoint. Librerías se importan bajo demanda.
"""

import os
from datetime import datetime
from typing import Optional


DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents")


class DocumentCreator:
    """Creador de documentos con carga diferida de librerías."""

    def __init__(self):
        self._docx = None
        self._openpyxl = None
        self._pptx = None

    def _get_docx(self):
        """Importa python-docx solo cuando se necesita."""
        if self._docx is None:
            from docx import Document as _d
            self._docx = _d
        return self._docx

    def _get_openpyxl(self):
        """Importa openpyxl solo cuando se necesita."""
        if self._openpyxl is None:
            import openpyxl as _o
            self._openpyxl = _o
        return self._openpyxl

    def _get_pptx(self):
        """Importa python-pptx solo cuando se necesita."""
        if self._pptx is None:
            from pptx import Presentation as _p
            self._pptx = _p
        return self._pptx

    def _ensure_docs_dir(self):
        """Asegura que existe el directorio de documentos."""
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        return DOCUMENTS_DIR

    def create_word(self, title: str, content: list, filename: Optional[str] = None) -> str:
        """Crea un documento Word. content es lista de strings (párrafos)."""
        Document = self._get_docx()
        doc = Document()
        doc.add_heading(title, level=1)
        for paragraph in content:
            doc.add_paragraph(paragraph)
        docs_dir = self._ensure_docs_dir()
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{title.replace(' ', '_')}_{ts}.docx"
        path = os.path.join(docs_dir, filename)
        doc.save(path)
        return path

    def create_excel(self, headers: list, rows: list, filename: Optional[str] = None) -> str:
        """Crea un archivo Excel con headers y filas de datos."""
        Workbook = self._get_openpyxl()
        wb = Workbook()
        ws = wb.active
        ws.title = "Datos"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        docs_dir = self._ensure_docs_dir()
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spreadsheet_{ts}.xlsx"
        path = os.path.join(docs_dir, filename)
        wb.save(path)
        return path

    def create_presentation(self, title: str, slides: list, filename: Optional[str] = None) -> str:
        """Crea una presentación PowerPoint. slides es lista de (titulo, contenido)."""
        Presentation = self._get_pptx()
        prs = Presentation()
        slide_layout = prs.slide_layouts[0]
        first_slide = prs.slides.add_slide(slide_layout)
        first_slide.shapes.title.text = title
        for slide_title, slide_content in slides:
            layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(layout)
            slide.shapes.title.text = slide_title
            slide.placeholders[1].text = slide_content
        docs_dir = self._ensure_docs_dir()
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{title.replace(' ', '_')}_{ts}.pptx"
        path = os.path.join(docs_dir, filename)
        prs.save(path)
        return path
