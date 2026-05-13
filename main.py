from typing import Sequence
from fastapi import FastAPI , status , Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session , selectinload 
from schemas import TodoCreateUpdate, TodoResponse, TaskCreate, TaskUpdate
from database import init_db , get_db
from models import Todo 
from models import Task 
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app : FastAPI):
    await init_db()
    yield 
    print("shutting down fastapi application") 

app = FastAPI(lifespan=lifespan)

@app.post("/api/todos",response_model=TodoResponse)
async def create_todo(todo : TodoCreateUpdate , db  = Depends(get_db)) -> Todo:
    title = todo.title
    new_todo = Todo(title=title)
    db.add(new_todo)
    await db.commit()
    await db.refresh(new_todo)
    return new_todo

@app.get("/api/todos",response_model=list[TodoResponse])
async def list_todo(db = Depends(get_db)) -> Sequence[Todo]:
    # return db.query(Todo).all()  this will trigger N + 1 query params 
    stmt = (
        select(Todo)
        .options(selectinload(Todo.tasks))
    )

    todos = await db.scalars(stmt)

    return todos.all()



@app.get("/api/todos/{todo_id}",response_model=TodoResponse)
async def get_todo(todo_id : int , db = Depends(get_db)) -> Todo:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        return existing_todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.patch("/api/todos/{todo_id}",response_model=TodoResponse)
async def update_todo(todo_id : int, todo : TodoCreateUpdate , db = Depends(get_db)) -> Todo:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        existing_todo.title = todo.title
        await db.commit()
        await db.refresh(existing_todo)
        return existing_todo 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.delete("/api/todos/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id : int , db = Depends(get_db)) -> None:
    existing_todo = await db.get(Todo,todo_id)
    if existing_todo:
        await db.delete(existing_todo)
        await db.commit()
        return 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.post("/api/todos/{todo_id}/tasks",response_model=TodoResponse)
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


@app.patch("/api/todos/{todo_id}/tasks/{task_id}",response_model=TodoResponse)
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
    

@app.delete("/api/todos/{todo_id}/tasks/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
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

    
