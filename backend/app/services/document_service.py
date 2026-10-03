import os
import re
import uuid
import logging
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import csv
import json
import pypdf
import docx
import openpyxl
from pptx import Presentation

from app.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
        """Validate file extension and size."""
        filename = file.filename or "uploaded_document"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return filename, ext

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        """Extract plain text from any supported document, spreadsheet, presentation, code, or text format."""
        text = ""
        ext = file_type.lower().replace(".", "")

        try:
            # 1. PDF Documents
            if ext == "pdf":
                reader = pypdf.PdfReader(file_path)
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    page_content = page.extract_text() or ""
                    if page_content.strip():
                        pages_text.append(page_content)
                text = "\n\n".join(pages_text)

            # 2. Word Documents (.docx)
            elif ext == "docx":
                doc = docx.Document(file_path)
                paras = [p.text for p in doc.paragraphs if p.text.strip()]
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join([c.text.strip() for c in row.cells if c.text.strip()])
                        if row_text:
                            paras.append(row_text)
                text = "\n\n".join(paras)

            # 3. PowerPoint Presentations (.pptx)
            elif ext == "pptx":
                prs = Presentation(file_path)
                slides_text = []
                for s_idx, slide in enumerate(prs.slides):
                    slide_lines = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_lines.append(shape.text.strip())
                    if slide_lines:
                        slides_text.append(f"[Slide {s_idx + 1}]\n" + "\n".join(slide_lines))
                text = "\n\n".join(slides_text)

            # 4. Excel Spreadsheets (.xlsx, .xls)
            elif ext in ["xlsx", "xls"]:
                wb = openpyxl.load_workbook(file_path, data_only=True)
                sheets_text = []
                for sheet_name in wb.sheetnames:
                    sheet = wb[sheet_name]
                    rows_text = []
                    for row in sheet.iter_rows(values_only=True):
                        # Filter out empty cells
                        row_values = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                        if row_values:
                            rows_text.append(" | ".join(row_values))
                    if rows_text:
                        sheets_text.append(f"[Sheet: {sheet_name}]\n" + "\n".join(rows_text))
                text = "\n\n".join(sheets_text)

            # 5. CSV Files (.csv)
            elif ext == "csv":
                csv_lines = []
                for enc in ["utf-8", "utf-8-sig", "latin-1"]:
                    try:
                        with open(file_path, "r", encoding=enc, errors="replace") as f:
                            reader = csv.reader(f)
                            for row in reader:
                                row_str = " | ".join([c.strip() for c in row if c.strip()])
                                if row_str:
                                    csv_lines.append(row_str)
                        break
                    except Exception:
                        continue
                text = "\n".join(csv_lines)

            # 6. JSON Data (.json)
            elif ext == "json":
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                    text = json.dumps(data, indent=2)

            # 7. Text, Markdown, and Code Files (.txt, .md, .py, .js, .ts, .html, .css, .xml, .yaml, .yml, .rtf, .log)
            elif ext in ["txt", "md", "py", "js", "ts", "html", "css", "xml", "yaml", "yml", "rtf", "log"]:
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            text = raw_data.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue

            # 8. Fallback for older binary documents (.doc, .ppt, etc.): extract readable text strings
            else:
                with open(file_path, "rb") as f:
                    raw_bytes = f.read()
                    # Extract printable ascii and utf-8 string sequences
                    printable = re.findall(rb"[\x20-\x7E\t\r\n]{4,}", raw_bytes)
                    text = "\n".join([p.decode("latin-1", errors="ignore").strip() for p in printable if p.strip()])

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise HTTPException(status_code=422, detail=f"Failed to extract text from document: {str(e)}")

        # Clean text
        text = DocumentService.clean_text(text)
        if not text.strip():
            raise HTTPException(status_code=400, detail="The document contains no readable text.")

        return text

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove null bytes
        text = text.replace("\x00", "")
        # Normalize newlines
        text = re.sub(r"\r\n|\r", "\n", text)
        # Normalize multiple spaces and multiple blank lines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """Split text into overlapping chunks respecting sentence/paragraph boundaries."""
        size = chunk_size or settings.CHUNK_SIZE
        overlap = chunk_overlap or settings.CHUNK_OVERLAP

        if len(text) <= size:
            return [text]

        # Split into paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If paragraph itself is larger than chunk_size, split by sentences or hard split
                if len(para) > size:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    sub_chunk = ""
                    for s in sentences:
                        if len(sub_chunk) + len(s) + 1 <= size:
                            sub_chunk = f"{sub_chunk} {s}".strip()
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = s
                    if sub_chunk:
                        current_chunk = sub_chunk
                    else:
                        current_chunk = ""
                else:
                    # Start new chunk with overlap from end of previous if possible
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Fallback if chunking produced empty list
        if not chunks:
            chunks = [text[:size]]

        return chunks

    @staticmethod
    def save_and_index_document(
        db: Session,
        file: UploadFile,
        title: str = None,
        conversation_id: str = None
    ) -> Document:
        """Save uploaded document file, extract text, chunk, embed, and store in DB."""
        filename, ext = DocumentService.validate_file(file)
        doc_title = title.strip() if title and title.strip() else filename

        # Unique file destination on disk
        unique_id = str(uuid.uuid4())
        safe_name = f"{unique_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

        # Check file size limit while saving
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        size = 0
        try:
            with open(file_path, "wb") as f:
                while chunk := file.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    f.write(chunk)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

        # Extract text
        text_content = DocumentService.extract_text(file_path, ext)

        # Create Document record
        doc = Document(
            id=unique_id,
            conversation_id=conversation_id,
            filename=filename,
            title=doc_title,
            file_type=ext.replace(".", ""),
            file_path=file_path,
            status="indexing",
            chunk_count=0
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            # Chunk and embed
            chunks = DocumentService.chunk_text(text_content)
            embeddings = embedding_service.get_embeddings(chunks)

            for idx, (chunk_text, emb) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_text,
                    embedding=emb
                )
                db.add(db_chunk)

            doc.status = "ready"
            doc.chunk_count = len(chunks)
            db.commit()
            db.refresh(doc)
            return doc
        except Exception as e:
            logger.error(f"Failed to index document {doc.id}: {e}")
            doc.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to process and index document: {str(e)}")

    @staticmethod
    def update_document(
        db: Session,
        document_id: str,
        title: str = None,
        new_content: str = None
    ) -> Document:
        """Update document metadata or text content, re-chunking and re-embedding."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if title:
            doc.title = title.strip()

        if new_content is not None and new_content.strip():
            cleaned = DocumentService.clean_text(new_content)
            # Delete old chunks
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            
            # Re-chunk and re-embed
            chunks = DocumentService.chunk_text(cleaned)
            embeddings = embedding_service.get_embeddings(chunks)

            for idx, (c_text, emb) in enumerate(zip(chunks, embeddings)):
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=c_text,
                    embedding=emb
                )
                db.add(db_chunk)

            doc.chunk_count = len(chunks)
            doc.status = "ready"

        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, document_id: str) -> bool:
        """Delete document, its chunks, and the file from disk."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete disk file
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.warning(f"Could not remove file {doc.file_path}: {e}")

        db.delete(doc)
        db.commit()
        return True

document_service = DocumentService()
