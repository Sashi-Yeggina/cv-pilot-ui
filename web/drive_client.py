"""
drive_client.py — Google Drive API integration for CV Pilot Web UI
------------------------------------------------------------------
Uses a Service Account (JSON key stored in Streamlit secrets) to:
  - List base CVs from Drive folder
  - Download CV files as bytes
  - Save aligned CVs back to Drive
  - Read/write cv_index.json on Drive

Folder structure on Google Drive:
  CV Pilot/
  ├── base_cvs/          ← Your 8+ source CVs (you upload once)
  ├── aligned_cvs/       ← Auto-saved aligned CVs
  └── cv_index.json      ← Tagging library (auto-managed)
"""

import io
import json
import time
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]


class DriveClient:
    """
    Google Drive client for CV Pilot.

    Args:
        credentials_json: Raw JSON string of service account key
        folder_name: Root folder name in Drive (default: "CV Pilot")
    """

    def __init__(self, credentials_json: str, folder_name: str = "CV Pilot"):
        self.folder_name = folder_name
        self._service = self._build_service(credentials_json)
        self._folder_ids: dict = {}   # cache: folder_name → id
        self._ensure_folder_structure()

    # ── Auth & Service ────────────────────────────────────────────────────────

    def _build_service(self, credentials_json: str):
        """Build Google Drive service from service account JSON string."""
        creds_dict = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    # ── Folder Management ─────────────────────────────────────────────────────

    def _find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Find a folder by name (optionally within a parent). Returns folder ID or None."""
        query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self._service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        return files[0]["id"] if files else None

    def _create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder and return its ID."""
        meta = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            meta["parents"] = [parent_id]

        folder = self._service.files().create(
            body=meta, fields="id"
        ).execute()
        return folder["id"]

    def _get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Get existing folder or create it. Uses in-memory cache."""
        cache_key = f"{parent_id or 'root'}/{name}"
        if cache_key in self._folder_ids:
            return self._folder_ids[cache_key]

        fid = self._find_folder(name, parent_id)
        if not fid:
            fid = self._create_folder(name, parent_id)

        self._folder_ids[cache_key] = fid
        return fid

    def _ensure_folder_structure(self):
        """Create the CV Pilot folder structure if it doesn't exist."""
        root_id = self._get_or_create_folder(self.folder_name)
        self._get_or_create_folder("base_cvs", root_id)
        self._get_or_create_folder("aligned_cvs", root_id)
        # cv_index.json is a file, not a folder — handled separately

    @property
    def root_folder_id(self) -> str:
        return self._get_or_create_folder(self.folder_name)

    @property
    def base_cvs_folder_id(self) -> str:
        return self._get_or_create_folder("base_cvs", self.root_folder_id)

    @property
    def aligned_cvs_folder_id(self) -> str:
        return self._get_or_create_folder("aligned_cvs", self.root_folder_id)

    # ── File Operations ───────────────────────────────────────────────────────

    def _list_files(self, folder_id: str, mime_type: Optional[str] = None) -> list:
        """List files in a folder. Returns list of dicts with id, name, size."""
        query = f"'{folder_id}' in parents and trashed=false"
        if mime_type:
            query += f" and mimeType='{mime_type}'"

        results = self._service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name, size, modifiedTime)",
            orderBy="name"
        ).execute()

        return results.get("files", [])

    def _download_file(self, file_id: str) -> bytes:
        """Download a file by ID and return its bytes."""
        request = self._service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buffer.getvalue()

    def extract_text_from_docx_bytes(self, docx_bytes: bytes) -> str:
        """
        Extract plain text from DOCX bytes.
        Used to read CV content for scoring.
        """
        from docx import Document
        import io

        doc = Document(io.BytesIO(docx_bytes))
        return "\n".join(para.text for para in doc.paragraphs)

    def read_cv_text(self, file_id: str) -> str:
        """
        Download a CV file and extract its text content.

        Args:
            file_id: Google Drive file ID of the DOCX CV

        Returns:
            Plain text content of the CV
        """
        docx_bytes = self._download_file(file_id)
        return self.extract_text_from_docx_bytes(docx_bytes)

    def _upload_file(
        self,
        filename: str,
        content: bytes,
        folder_id: str,
        mime_type: str = "application/octet-stream",
        existing_file_id: Optional[str] = None
    ) -> str:
        """Upload or update a file. Returns file ID."""
        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype=mime_type,
            resumable=False
        )

        if existing_file_id:
            # Update existing file
            file = self._service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields="id"
            ).execute()
        else:
            # Create new file
            meta = {"name": filename, "parents": [folder_id]}
            file = self._service.files().create(
                body=meta,
                media_body=media,
                fields="id"
            ).execute()

        return file["id"]

    def _find_file(self, filename: str, folder_id: str) -> Optional[str]:
        """Find a file by name in a folder. Returns file ID or None."""
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = self._service.files().list(
            q=query,
            spaces="drive",
            fields="files(id)"
        ).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    # ── Public API ────────────────────────────────────────────────────────────

    def list_base_cvs(self) -> list:
        """
        List all base CVs in Drive.
        Returns list of dicts: [{id, name, size, modifiedTime}, ...]
        """
        files = self._list_files(self.base_cvs_folder_id)
        # Filter to DOCX only
        return [f for f in files if f["name"].lower().endswith(".docx")]

    def download_cv(self, file_id: str) -> bytes:
        """Download a CV file as bytes."""
        return self._download_file(file_id)

    def save_aligned_cv(self, filename: str, content: bytes) -> str:
        """
        Save an aligned CV to the aligned_cvs/ folder.
        If a file with the same name exists, it is overwritten.
        Returns the Drive file ID.
        """
        existing_id = self._find_file(filename, self.aligned_cvs_folder_id)
        return self._upload_file(
            filename=filename,
            content=content,
            folder_id=self.aligned_cvs_folder_id,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            existing_file_id=existing_id
        )

    def get_aligned_cv_link(self, file_id: str) -> str:
        """Return a shareable Google Drive link for an aligned CV."""
        return f"https://drive.google.com/file/d/{file_id}/view"

    # ── Index Management ──────────────────────────────────────────────────────

    def load_index(self) -> list:
        """
        Load cv_index.json from Drive root folder.
        Returns list of CV index entries. Empty list if not found.
        """
        file_id = self._find_file("cv_index.json", self.root_folder_id)
        if not file_id:
            return []

        try:
            data = self._download_file(file_id)
            return json.loads(data.decode("utf-8"))
        except Exception:
            return []

    def update_index(self, index: list) -> None:
        """
        Save updated cv_index.json to Drive.
        Creates or overwrites the file.
        """
        content = json.dumps(index, indent=2).encode("utf-8")
        existing_id = self._find_file("cv_index.json", self.root_folder_id)
        self._upload_file(
            filename="cv_index.json",
            content=content,
            folder_id=self.root_folder_id,
            mime_type="application/json",
            existing_file_id=existing_id
        )

    # ── Reuse Check ───────────────────────────────────────────────────────────

    def find_reusable_cv(
        self,
        index: list,
        jd_keywords: list,
        role_category: str,
        threshold: float = 0.75
    ) -> Optional[dict]:
        """
        Check if a sufficiently similar aligned CV already exists in the index.
        Returns the index entry if match score >= threshold, else None.
        """
        if not index or not jd_keywords:
            return None

        jd_kw_set = {kw.lower() for kw in jd_keywords}

        best_match = None
        best_score = 0.0

        for entry in index:
            # Category filter
            if entry.get("role_category", "").lower() != role_category.lower():
                continue

            entry_keywords = {kw.lower() for kw in entry.get("jd_keywords", [])}
            if not entry_keywords:
                continue

            # Jaccard similarity
            intersection = len(jd_kw_set & entry_keywords)
            union = len(jd_kw_set | entry_keywords)
            score = intersection / union if union > 0 else 0.0

            if score > best_score:
                best_score = score
                best_match = entry

        return best_match if best_score >= threshold else None

    def get_template_cv(self) -> Optional[bytes]:
        """
        Download _template.docx from the CV Pilot root folder if it exists.

        Upload a file named '_template.docx' to your 'CV Pilot/' folder in
        Google Drive to define the design (fonts, layout, section structure)
        for all generated CVs. If not found, the best-matching base CV is
        used for formatting instead.

        Returns:
            bytes of the template DOCX, or None if not uploaded yet.
        """
        file_id = self._find_file("_template.docx", self.root_folder_id)
        if not file_id:
            return None
        return self._download_file(file_id)

    def get_aligned_cv_bytes(self, filename: str) -> Optional[bytes]:
        """
        Download a specific aligned CV from Drive by filename.
        Returns bytes or None if not found.
        """
        file_id = self._find_file(filename, self.aligned_cvs_folder_id)
        if not file_id:
            return None
        return self._download_file(file_id)
