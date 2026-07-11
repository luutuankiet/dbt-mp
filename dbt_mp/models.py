from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SlimColumn(BaseModel):
    """A slimmed-down column definition (from a model or source)."""
    name: Optional[str] = Field(
        default=None,
        description="Column name as it appears in the warehouse table"
    )
    description: Optional[str] = Field(
        default=None,
        description="Documented meaning of the column, if provided in the dbt project"
    )
    data_type: Optional[str] = Field(
        default=None,
        description="Column data type, when declared in the dbt project (may be absent)"
    )


class SlimNodeConfig(BaseModel):
    """Configuration subset for a dbt node."""
    materialized: Optional[str] = Field(
        default=None, 
        description="Materialization strategy: table, view, incremental, ephemeral"
    )
    enabled: Optional[bool] = Field(
        default=None,
        description="Whether this model is enabled in the dbt project"
    )
    incremental_strategy: Optional[str] = Field(
        default=None,
        description="For incremental models: merge, delete+insert, append, etc."
    )

class SlimNode(BaseModel):
    """A slimmed-down dbt node (model/snapshot/seed) optimized for LLM context."""
    schema_name: Optional[str] = Field(
        default=None, 
        alias="schema",
        description="Database schema where this model materializes"
    )
    name: Optional[str] = Field(
        default=None,
        description="Short model name without project prefix"
    )
    resource_type: Optional[str] = Field(
        default=None,
        description="Resource type: model, snapshot, seed, test"
    )
    unique_id: Optional[str] = Field(
        default=None,
        description="Fully qualified name (e.g., model.project.model_name) - use as lookup key"
    )
    relation_name: Optional[str] = Field(
        default=None,
        description="Fully-qualified, quoted warehouse relation (e.g. \"db\".\"schema\".\"table\") - the exact identifier to put in a FROM clause when querying this model in the data warehouse"
    )
    config: Optional[SlimNodeConfig] = Field(
        default=None,
        description="Model configuration subset"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags applied to this model for selection/organization"
    )
    columns: Optional[Dict[str, SlimColumn]] = Field(
        default=None,
        description="Documented columns this model emits, keyed by column name. Only populated when declared in the dbt project - inspect for the model's output schema"
    )
    raw_code: Optional[str] = Field(
        default=None,
        description="Original Jinja/SQL source code with unresolved ref() and source() calls"
    )
    refs: Optional[List[Any]] = Field(
        default=None,
        description="List of models referenced via ref() - use to trace upstream dependencies"
    )
    sources: Optional[List[Any]] = Field(
        default=None,
        description="List of sources referenced via source() - use to find raw data origins"
    )
    depends_on: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Upstream dependencies: .nodes[] for model refs, .macros[] for macro usage"
    )
    compiled_code: Optional[str] = Field(
        default=None,
        description="Resolved SQL after Jinja compilation - inspect for grain, joins, transformations"
    )

class SlimSource(BaseModel):
    """A slimmed-down dbt source definition."""
    database: Optional[str] = Field(
        default=None,
        description="Database name where the source table resides"
    )
    schema_name: Optional[str] = Field(
        default=None,
        alias="schema",
        description="Schema name where the source table resides"
    )
    name: Optional[str] = Field(
        default=None,
        description="Source table name"
    )
    unique_id: Optional[str] = Field(
        default=None,
        description="Fully qualified source ID (e.g., source.project.source_name.table_name)"
    )
    relation_name: Optional[str] = Field(
        default=None,
        description="Fully-qualified, quoted warehouse relation (e.g. \"db\".\"schema\".\"table\") - the exact identifier to put in a FROM clause when querying this source in the data warehouse"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the source table"
    )
    columns: Optional[Dict[str, SlimColumn]] = Field(
        default=None,
        description="Documented columns this source emits, keyed by column name. Only populated when declared in the dbt project - inspect to understand what the source table provides"
    )

class SlimMacro(BaseModel):
    """A slimmed-down dbt macro definition."""
    unique_id: Optional[str] = Field(
        default=None,
        description="Fully qualified macro ID (e.g., macro.project.macro_name)"
    )
    macro_sql: Optional[str] = Field(
        default=None,
        description="The SQL/Jinja code of the macro"
    )