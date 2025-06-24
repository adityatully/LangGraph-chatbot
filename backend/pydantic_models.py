from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# defind structures or models of the data should flow # through the application using Pydantic

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    
class DocumentInfo(BaseModel):
    id: int
    filename: str
    session_id: str
    upload_timestamp: datetime


class DeleteFileRequest(BaseModel):
    file_id: int
