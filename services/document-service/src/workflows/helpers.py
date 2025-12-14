"""Helper functions for document processing"""
from pathlib import Path
import PyPDF2
from docx import Document as DocxDocument

def read_document(file_path: str) -> str:
    """Read PDF or DOCX and return text"""
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    elif path.suffix.lower() == ".docx":
        return read_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

def read_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    text = []
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

    return "\n".join(text)

def read_docx(file_path: str) -> str:
    """Extract text from DOCX"""
    try:
        doc = DocxDocument(file_path)
        text = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(text)
    except Exception as e:
        raise ValueError(f"Error reading DOCX: {str(e)}")

def load_extraction_prompt(doc_type: str) -> str:
    """Load prompt template for document type"""
    prompts = {
        "FACILITY_AGREEMENT": """You are an expert loan document analyst. Extract the following from this LMA Facility Agreement:

1. BORROWER:
   - Legal name
   - Jurisdiction

2. FACILITY:
   - Total amount and currency
   - Facility type (Term Loan, RCF, etc.)
   - Tenor/maturity date
   - Interest rate (SONIA/EURIBOR + margin)

3. FINANCIAL COVENANTS (if any):
   - Covenant type (Leverage, Interest Cover, etc.)
   - Definition
   - Threshold
   - Testing frequency

Return ONLY valid JSON with this exact structure (no markdown, no explanations):
{
  "borrower": {"name": "Company Name Ltd", "jurisdiction": "England and Wales"},
  "facility": {"amount": 100000000, "currency": "GBP", "type": "Term Loan", "maturity_date": "2028-12-31", "interest_rate": "SONIA + 2.5%"},
  "covenants": [{"type": "Leverage Ratio", "definition": "Total Net Debt to EBITDA", "threshold": 3.5, "frequency": "Quarterly"}]
}""",

        "AMENDMENT": """Extract amendment details:
1. Original agreement date
2. Amendment number
3. Changes being made
4. Effective date

Return ONLY valid JSON (no markdown):
{
  "original_date": "2023-01-15",
  "amendment_number": 1,
  "changes": "Increase facility amount",
  "effective_date": "2024-06-01"
}""",

        "TERM_SHEET": """Extract term sheet details:
1. Proposed borrower
2. Facility amount and type
3. Key terms
4. Conditions precedent

Return ONLY valid JSON (no markdown):
{
  "borrower": "Company Name",
  "facility_amount": 50000000,
  "facility_type": "Revolving Credit Facility",
  "key_terms": "3-year tenor, quarterly payments",
  "conditions": "Board approval, KYC completion"
}"""
    }

    return prompts.get(doc_type, prompts["FACILITY_AGREEMENT"])
