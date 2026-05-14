from fastapi import status , Depends , APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from schemas import  TodoResponse, TaskCreate, TaskUpdate
from database import get_db
from models import Todo 
from models import Task 


router = APIRouter()

@router.post("",response_model=TodoResponse)
async def create_task(todo_id : int , task : TaskCreate , db = Depends(get_db))->Todo:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        text = task.text
        new_task = Task(text=text,todo_id=existing_todo.id)
        db.add(new_task)
        await db.commit()
        await db.refresh(existing_todo)
        return existing_todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")


@router.patch("/{task_id}",response_model=TodoResponse)
async def update_task(todo_id : int , task_id : int , task : TaskUpdate , db = Depends(get_db))->Todo:
    stmt = select(Task).where(
        Task.id == task_id,
        Task.todo_id == todo_id 
    )
    existing_task = await db.scalar(stmt)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    update_data = task.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields for updation is provided"
        )
    
    for key,value in update_data.items():
        setattr(existing_task,key,value)
    
    await db.commit()
    await db.refresh(existing_task)
    return existing_task.todo
    

@router.delete("/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(todo_id : int , task_id : int , db = Depends(get_db)) -> None:
    stmt = select(Task).where(
        Task.id == task_id,
        Task.todo_id == todo_id 
    )   
    existing_task = await db.scalar(stmt)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    await db.delete(existing_task)
    await db.commit()
    return 