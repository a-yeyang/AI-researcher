import os
import requests
import tempfile
from urllib.parse import urlparse
from langchain_community.document_loaders import PyMuPDFLoader


class PyMuPDFScraper:

    def __init__(self, link, session=None):
        """
        Initialize the scraper with a link and an optional session.

        Args:
          link (str): The URL or local file path of the PDF document.
          session (requests.Session, optional): An optional session for making HTTP requests.
        """
        self.link = link
        self.session = session

    def is_url(self) -> bool:
        """
        Check if the provided `link` is a valid URL.

        Returns:
          bool: True if the link is a valid URL, False otherwise.
        """
        try:
            result = urlparse(self.link)
            return all([result.scheme, result.netloc])  # Check for valid scheme and network location
        except Exception:
            return False

    def scrape(self) -> tuple[str, list[str], str]:
        """
        The `scrape` function uses PyMuPDFLoader to load a document from the provided link (either URL or local file)
        and returns the document as a string.

        Returns:
          str: A string representation of the loaded document.
        """
        try:
            if self.is_url():
                response = requests.get(self.link, timeout=5, stream=True)
                response.raise_for_status()

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_filename = temp_file.name  # Get the temporary file name
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)  # Write the downloaded content to the temporary file

                loader = PyMuPDFLoader(temp_filename)
                doc = loader.load()

                os.remove(temp_filename)
            else:
                loader = PyMuPDFLoader(self.link)
                doc = loader.load()

            # Extract all pages with a conservative cap to avoid context explosion.
            image = []
            max_chars = int(os.getenv("PDF_FULLTEXT_MAX_CHARS", "120000"))
            page_texts = []
            total_chars = 0

            for page_index, page in enumerate(doc, start=1):
                content = (page.page_content or "").strip()
                if not content:
                    continue
                block = f"[Page {page_index}]\n{content}"
                page_texts.append(block)
                total_chars += len(block)
                if total_chars >= max_chars:
                    break

            full_content = "\n\n".join(page_texts).strip()
            if not full_content:
                return "", image, ""

            title = ""
            for page in doc:
                title = page.metadata.get("title", "") if page.metadata else ""
                if title:
                    break
            return full_content, image, title

        except requests.exceptions.Timeout:
            print(f"Download timed out. Please check the link : {self.link}")
            return "", [], ""
        except Exception as e:
            print(f"Error loading PDF : {self.link} {e}")
            return "", [], ""
