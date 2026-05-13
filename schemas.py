from pydantic import BaseModel , Field , ConfigDict
from pydantic.types import Enum
from pydantic.types import datetime


class TaskResponse(BaseModel):
    id : int 
    text : str = Field(min_length=1)
    completed : bool = False 
    created_at : datetime 

    model_config = ConfigDict(
        from_attributes=True
    )
    
class TodoResponse(BaseModel):
    id : int
    title : str = Field(min_length=1,max_length=100) 
    tasks : list[TaskResponse] = []
    created_at : datetime 
    model_config = ConfigDict(
        from_attributes=True
    )

class TaskCreate(BaseModel):
    text : str = Field(min_length=1)

class TaskUpdate(BaseModel):
    text : str | None = None 
    completed : bool | None = None 
    
class TodoCreateUpdate(BaseModel):
    title : str = Field(min_length=1,max_length=100) 
    






