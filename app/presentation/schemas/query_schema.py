from pydantic import BaseModel
from typing import List, Optional


class QueryStatSchema(BaseModel):
    query: str
    mean_time: float
    calls: int
    total_time: float
    rows: Optional[int] = None


class QueriesResponse(BaseModel):
    slow_queries: List[QueryStatSchema]
    frequent_queries: List[QueryStatSchema]
    heaviest_queries: List[QueryStatSchema]
