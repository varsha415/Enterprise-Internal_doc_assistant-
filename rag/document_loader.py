"""Document loader and chunking for Acme Tech RAG."""
import re
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    role_access: str
    department: str
    section: str
    chunk_index: int
    content: str

    def to_chroma_metadata(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "role_access": self.role_access.lower().strip(),
            "department": self.department,
            "section": self.section,
            "chunk_index": self.chunk_index
        }

def parse_markdown_frontmatter(file_content: str) -> tuple[Dict[str, str], str]:
    """Extract frontmatter and body from markdown text."""
    frontmatter: Dict[str, str] = {}
    body = file_content

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", file_content, re.DOTALL)
    if fm_match:
        raw_fm, body = fm_match.groups()
        for line in raw_fm.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                frontmatter[key.strip()] = val.strip().strip('"').strip("'")

    return frontmatter, body.strip()

def split_into_sections(body: str, default_title: str) -> List[tuple[str, str]]:
    """Splits markdown text into (section_header, text) tuples."""
    lines = body.splitlines()
    sections: List[tuple[str, str]] = []
    current_header = default_title
    current_lines: List[str] = []

    for line in lines:
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append((current_header, sec_text))
            current_header = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append((current_header, sec_text))

    return sections

def load_document_file(file_path: Path) -> List[DocumentChunk]:
    """Reads a markdown file and decomposes it into metadata-tagged chunks."""
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_markdown_frontmatter(content)

    doc_id = fm.get("id", file_path.stem)
    doc_title = fm.get("title", file_path.stem.replace("_", " ").title())
    role_access = fm.get("role_access", "all").lower().strip()
    department = fm.get("department", "General")

    raw_sections = split_into_sections(body, default_title=doc_title)
    chunks: List[DocumentChunk] = []
    chunk_index = 0

    for sec_header, sec_text in raw_sections:
        # If section is small/medium, keep as single chunk. If > 900 chars, split by paragraphs
        paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
        current_chunk_text = ""

        for p in paragraphs:
            if len(current_chunk_text) + len(p) > 800 and current_chunk_text:
                chunk_id = f"{doc_id}-chunk-{chunk_index}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    doc_title=doc_title,
                    role_access=role_access,
                    department=department,
                    section=sec_header,
                    chunk_index=chunk_index,
                    content=current_chunk_text.strip()
                ))
                chunk_index += 1
                current_chunk_text = f"[{sec_header}]\n{p}\n"
            else:
                if not current_chunk_text:
                    current_chunk_text = f"[{sec_header}]\n{p}\n"
                else:
                    current_chunk_text += f"\n{p}\n"

        if current_chunk_text.strip():
            chunk_id = f"{doc_id}-chunk-{chunk_index}"
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                doc_title=doc_title,
                role_access=role_access,
                department=department,
                section=sec_header,
                chunk_index=chunk_index,
                content=current_chunk_text.strip()
            ))
            chunk_index += 1

    return chunks

def load_all_documents(docs_dir: Path) -> List[DocumentChunk]:
    """Loads and chunks all markdown files from the target directory."""
    all_chunks: List[DocumentChunk] = []
    for md_file in sorted(docs_dir.glob("*.md")):
        all_chunks.extend(load_document_file(md_file))
    return all_chunks
