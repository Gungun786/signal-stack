import io
import logging
from typing import List, Dict, Any
import pandas as pd
from pypdf import PdfReader

logger = logging.getLogger("signal_stack.internal")

class InternalDocumentParser:
    """Parses uploaded internal sales, feedback, and support documents."""

    def parse_file(self, filename: str, content_bytes: bytes) -> List[Dict[str, Any]]:
        filename_lower = filename.lower()
        items = []

        try:
            if filename_lower.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content_bytes))
                items.extend(self._process_dataframe(df, filename))
            elif filename_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content_bytes))
                items.extend(self._process_dataframe(df, filename))
            elif filename_lower.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(content_bytes))
                full_text = ""
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    full_text += f"\n--- Page {page_idx+1} ---\n{text}"
                items.append({
                    "title": f"Internal Doc: {filename}",
                    "content": full_text[:4000],
                    "type": "internal_document"
                })
            else: # Plain text / markdown
                text = content_bytes.decode("utf-8", errors="ignore")
                items.append({
                    "title": f"Internal Note: {filename}",
                    "content": text[:4000],
                    "type": "internal_notes"
                })
        except Exception as e:
            logger.error(f"Failed to parse internal file {filename}: {e}")

        return items

    def _process_dataframe(self, df: pd.DataFrame, filename: str) -> List[Dict[str, Any]]:
        items = []
        # Convert first 50 rows to record summaries
        for idx, row in df.head(50).iterrows():
            summary_parts = [f"{col}: {val}" for col, val in row.items() if pd.notna(val)]
            snippet = " | ".join(summary_parts[:6])
            items.append({
                "title": f"Internal Record #{idx+1} ({filename})",
                "content": snippet[:800],
                "type": "internal_data_row"
            })
        return items

internal_parser = InternalDocumentParser()
