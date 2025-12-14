"""LangGraph-based extraction workflow for LMA Synapse"""
import os
import json
import logging
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .helpers import read_document, load_extraction_prompt
from ..database.jobs import update_job_status
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

# Initialize Gemini models
flash_llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_FLASH_MODEL,
    temperature=0.1,
    google_api_key=settings.GEMINI_API_KEY
)

pro_llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_PRO_MODEL,
    temperature=0.1,
    google_api_key=settings.GEMINI_API_KEY
)

class ExtractionState(TypedDict):
    """Shared state passed between agents"""
    job_id: str
    document_path: str
    document_type: str
    raw_text: str
    gemini_extraction: dict
    normalized_data: dict
    confidence_score: float
    errors: Annotated[list, operator.add]  # Accumulate errors

# Agent 1: Document Classifier
def classify_document_agent(state: ExtractionState) -> ExtractionState:
    """Classify document type using Gemini Flash (fast + cheap)"""
    logger.info(f"[Job {state['job_id']}] Classifying document...")

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a loan document classifier. Classify this document as one of:
- FACILITY_AGREEMENT
- AMENDMENT
- TERM_SHEET
- COMMITMENT_LETTER
- OTHER

Respond with ONLY the classification, nothing else."""),
            ("user", "Document text (first 2000 chars):\n\n{text}")
        ])

        # Read document
        raw_text = read_document(state["document_path"])
        logger.info(f"[Job {state['job_id']}] Document read successfully. Length: {len(raw_text)} chars")

        # Classify
        chain = prompt | flash_llm
        result = chain.invoke({"text": raw_text[:2000]})
        doc_type = result.content.strip()

        logger.info(f"[Job {state['job_id']}] Classified as: {doc_type}")

        return {
            **state,
            "raw_text": raw_text,
            "document_type": doc_type
        }

    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Classification error: {str(e)}")
        return {
            **state,
            "document_type": "UNKNOWN",
            "raw_text": "",
            "errors": [f"Classification failed: {str(e)}"]
        }

# Agent 2: Gemini Extraction
def gemini_extraction_agent(state: ExtractionState) -> ExtractionState:
    """Extract structured data using Gemini Pro"""
    logger.info(f"[Job {state['job_id']}] Extracting data with Gemini Pro...")

    try:
        # Load prompt template based on doc type
        prompt_template = load_extraction_prompt(state["document_type"])

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("user", "{document_text}")
        ])

        # Use Pro model for extraction
        chain = prompt | pro_llm

        # Truncate document if too long (Gemini has token limits)
        max_chars = 30000  # Approximately 7500 tokens
        doc_text = state["raw_text"][:max_chars]

        result = chain.invoke({"document_text": doc_text})

        # Parse JSON from response
        response_text = result.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        extraction = json.loads(response_text.strip())

        logger.info(f"[Job {state['job_id']}] Extraction successful")

        return {
            **state,
            "gemini_extraction": extraction,
            "confidence_score": 0.85  # Initial estimate
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Job {state['job_id']}] JSON parsing error: {str(e)}")
        logger.error(f"Response was: {result.content[:500]}")
        return {
            **state,
            "gemini_extraction": {},
            "confidence_score": 0.0,
            "errors": [f"JSON parsing failed: {str(e)}"]
        }

    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Extraction error: {str(e)}")
        return {
            **state,
            "gemini_extraction": {},
            "confidence_score": 0.0,
            "errors": [f"Extraction failed: {str(e)}"]
        }

# Agent 3: Data Fusion
def data_fusion_agent(state: ExtractionState) -> ExtractionState:
    """Fuse Gemini and LayoutLM extractions (if available)"""
    logger.info(f"[Job {state['job_id']}] Fusing extraction results...")

    # For MVP, just use Gemini extraction
    fused = state["gemini_extraction"]

    # TODO: Add LayoutLM fusion logic post-MVP

    return {
        **state,
        "fused_data": fused
    }

# Agent 4: Normalization
def normalization_agent(state: ExtractionState) -> ExtractionState:
    """Normalize to LMA ontology schema"""
    logger.info(f"[Job {state['job_id']}] Normalizing data to LMA ontology...")

    try:
        # For MVP, minimal normalization
        # Just ensure standard field names and add metadata
        normalized = {
            "document_type": state["document_type"],
            "extraction": state["fused_data"],
            "ontology_version": "1.0.0-mvp",
            "source": "gemini-extraction"
        }

        # Calculate confidence based on completeness
        required_fields = set()
        if state["document_type"] == "FACILITY_AGREEMENT":
            required_fields = {"borrower", "facility"}

        extracted_fields = set(state["fused_data"].keys())
        completeness = len(required_fields & extracted_fields) / max(len(required_fields), 1)

        confidence = state["confidence_score"] * (0.5 + 0.5 * completeness)

        logger.info(f"[Job {state['job_id']}] Normalization complete. Confidence: {confidence:.2f}")

        return {
            **state,
            "normalized_data": normalized,
            "confidence_score": confidence
        }

    except Exception as e:
        logger.error(f"[Job {state['job_id']}] Normalization error: {str(e)}")
        return {
            **state,
            "normalized_data": state["fused_data"],
            "errors": [f"Normalization failed: {str(e)}"]
        }

# Agent 5: Validation
def validation_agent(state: ExtractionState) -> ExtractionState:
    """Validate against schema and business rules"""
    logger.info(f"[Job {state['job_id']}] Validating extraction...")

    # For MVP, basic validation
    validation_errors = []

    # Check if extraction has any data
    if not state["normalized_data"].get("extraction"):
        validation_errors.append("No data extracted from document")

    # Check confidence threshold
    if state["confidence_score"] < 0.3:
        validation_errors.append(f"Low confidence: {state['confidence_score']:.2f}")

    if validation_errors:
        logger.warning(f"[Job {state['job_id']}] Validation warnings: {validation_errors}")
        return {
            **state,
            "errors": validation_errors,
            "confidence_score": state["confidence_score"] * 0.8  # Penalize
        }

    logger.info(f"[Job {state['job_id']}] Validation passed")
    return state

# Build workflow
def create_extraction_workflow():
    """Create and compile LangGraph workflow"""

    workflow = StateGraph(ExtractionState)

    # Add nodes (agents)
    workflow.add_node("classify", classify_document_agent)
    workflow.add_node("extract_gemini", gemini_extraction_agent)
    workflow.add_node("fuse", data_fusion_agent)
    workflow.add_node("normalize", normalization_agent)
    workflow.add_node("validate", validation_agent)

    # Define flow
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "extract_gemini")
    workflow.add_edge("extract_gemini", "fuse")
    workflow.add_edge("fuse", "normalize")
    workflow.add_edge("normalize", "validate")
    workflow.add_edge("validate", END)

    return workflow.compile()

# Main execution function
async def run_extraction_workflow(job_id: str, file_path: str):
    """Run the complete extraction workflow"""
    logger.info(f"[Job {job_id}] Starting extraction workflow for: {file_path}")

    try:
        # Update status to processing
        await update_job_status(job_id, status="processing", progress=0)

        # Create workflow
        app = create_extraction_workflow()

        # Initial state
        initial_state = {
            "job_id": job_id,
            "document_path": file_path,
            "document_type": "",
            "raw_text": "",
            "gemini_extraction": {},
            "normalized_data": {},
            "confidence_score": 0.0,
            "errors": []
        }

        # Run workflow (synchronous call wrapped in async)
        result = app.invoke(initial_state)

        logger.info(f"[Job {job_id}] Workflow complete. Final confidence: {result['confidence_score']:.2f}")

        # Save results
        await update_job_status(
            job_id=job_id,
            status="completed",
            progress=100,
            result=result["normalized_data"],
            confidence=result["confidence_score"]
        )

        if result["errors"]:
            logger.warning(f"[Job {job_id}] Completed with errors: {result['errors']}")

    except Exception as e:
        logger.error(f"[Job {job_id}] Workflow failed: {str(e)}", exc_info=True)
        await update_job_status(
            job_id=job_id,
            status="failed",
            error=str(e)
        )
