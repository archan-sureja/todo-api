from pydantic import BaseModel , Field , field_validator
from pydantic.types import Enum
from pydantic.types import datetime 

class TaskStatus(str,Enum):
    PENDING = "pending"
    INPROGRESS = "in-progres"
    COMPLETED = "completed"

class Task(BaseModel):
    id : int 
    text : str = Field(min_length=1)
    status : TaskStatus = TaskStatus.PENDING 
    created_at : datetime = datetime.now()

class Todo(BaseModel):
    id : int
    title : str = Field(min_length=1,max_length=100) 
    tasks : list[Task] = []
    created_at : datetime = datetime.now()

class TaskCreate(BaseModel):
    text : str = Field(min_length=1)

class TaskUpdate(BaseModel):
    text : str | None = None 
    status : TaskStatus | None = None 
    
class TodoCreateUpdate(BaseModel):
    title : str = Field(min_length=1,max_length=100) 
    






