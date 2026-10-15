from pydantic import BaseModel, Field, create_model
from typing import Optional, Literal, List
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src import config
import json

class ChunkExtractionMetadata(BaseModel):
    company: Optional[str] = Field(None, description="Company name")
    document_type: Optional[str] = Field(None, description="Type of the financial document")
    period: Optional[str] = Field(None, description="what time period does the financial document belongs to, ex: financial year 23-24")

class QueryIntent(BaseModel):
    search_query: str = Field(..., description="cleaned semantic query text, stripout metadata keywords like company name, document type, period")
    filters: ChunkExtractionMetadata

class QueryIntentList(BaseModel):
    is_multi_part: bool = Field(
        ...,
        description="Set to True if the query splits into multiple sub-queries"
    )
    sub_queries: List[QueryIntent] = Field(
        ...,
        description="List of targeted sub queries to execute against Qdrant"
    )

def get_qdrant_filter(filters) -> Optional[Filter]:
    must_conditions = []

    if filters.company:
        must_conditions.append(FieldCondition(key="company", match=MatchValue(value=filters.company)))
    if filters.document_type:
        must_conditions.append(FieldCondition(key="document_type", match=MatchValue(value=filters.document_type)))
    if filters.period:
        must_conditions.append(FieldCondition(key="period", match=MatchValue(value=filters.period)))
    return Filter(must=must_conditions) if must_conditions else None

def build_schema(catelogue):
    MetadataModel = create_model(
        'ExtractedModel',
        company=(Optional[Literal[tuple(catelogue.get('company', []))]], Field(None, description="Company name")),
        document_type=(Optional[Literal[tuple(catelogue.get('document_type', []))]], Field(None, description="financial document type")),
        period=(Optional[Literal[tuple(catelogue.get('period', []))]], Field(None, description="time period of the financial document"))
    )
    QueryModel = create_model(
        'QueryModel',
        search_query = (str, Field(..., description="cleaned semantic query text, stripout metadata keywords like company name, document type, period")),
        filters=(MetadataModel, Field(..., description="Extracted catalog metadata"))
    )

    DecomposerQueryPlan = create_model(
        'QueryModel',
        is_multi_part=(bool, Field(..., description="Set True if the query splits to multiple search queries")),
        sub_queries=(
            List[QueryModel],
            Field(..., description="List of targeted sub-queries to run against Qdrant")
        )
    )

    return DecomposerQueryPlan


def get_system_prompt():
    schema_json_data = json.dumps(QueryIntent.model_json_schema(), indent=2)
    return f"""{config.metadata_filter_prompt}
{schema_json_data}

{config.metadata_filter_rule_prompt}
"""