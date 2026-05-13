from typing import Sequence
from fastapi import status,Depends , APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import  selectinload 
from schemas import TodoCreateUpdate, TodoResponse
from database import get_db
from models import Todo 


router = APIRouter()
@router.post("",response_model=TodoResponse)
async def create_todo(todo : TodoCreateUpdate , db  = Depends(get_db)) -> Todo:
    title = todo.title
    new_todo = Todo(title=title)
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo

@router.get("",response_model=list[TodoResponse])
async def list_todo(db = Depends(get_db)) -> Sequence[Todo]:
    # return db.query(Todo).all()  this will trigger N + 1 query params 
    stmt = (
        select(Todo)
        .options(selectinload(Todo.tasks))
    )

    todos = await db.scalars(stmt)

    return todos.all()

@router.get("/{todo_id}",response_model=TodoResponse)
async def get_todo(todo_id : int , db = Depends(get_db)) -> Todo:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        return existing_todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@router.patch("/{todo_id}",response_model=TodoResponse)
async def update_todo(todo_id : int, todo : TodoCreateUpdate , db = Depends(get_db)) -> Todo:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        existing_todo.title = todo.title
        await db.commit()
        await db.refresh(existing_todo)
        return existing_todo 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@router.delete("/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id : int , db = Depends(get_db)) -> None:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        await db.delete(existing_todo)
        await db.commit()
        return 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")