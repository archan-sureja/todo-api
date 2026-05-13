from fastapi import FastAPI , status , Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session , selectinload 
from schemas import TodoCreateUpdate, TodoResponse, TaskCreate, TaskResponse, TaskUpdate
from database import init_db , get_db
from models import Todo 
from models import Task 


def lifespan(app : FastAPI):
    init_db()
    yield 
    print("shutting down fastapi application") 

app = FastAPI(lifespan=lifespan)

@app.post("/api/todos",response_model=TodoResponse)
def create_todo(todo : TodoCreateUpdate , db : Session = Depends(get_db)) -> TodoResponse:
    title = todo.title
    new_todo = Todo(title=title)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@app.get("/api/todos")
def list_todo(db : Session = Depends(get_db)) -> list[TodoResponse]:
    # return db.query(Todo).all()  this will trigger N + 1 query params 
    stmt = (
        select(Todo)
        .options(selectinload(Todo.tasks))
    )

    todos = db.scalars(stmt).all()

    return todos


@app.get("/api/todos/{todo_id}")
def get_todo(todo_id : int , db : Session = Depends(get_db)) -> TodoResponse:
    existing_todo = db.get(Todo,todo_id)
    if existing_todo:
        return existing_todo 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id : int, todo : TodoCreateUpdate , db : Session = Depends(get_db)) -> TodoResponse:
    existing_todo = db.get(Todo,todo_id)
    if existing_todo:
        existing_todo.title = todo.title
        db.commit()
        db.refresh(existing_todo)
        return existing_todo 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.delete("/api/todos/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id : int , db : Session = Depends(get_db)) -> None:
    existing_todo = db.get(Todo,todo_id)
    if existing_todo:
        db.delete(existing_todo)
        db.commit()
        return 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.post("/api/todos/{todo_id}/tasks",response_model=TodoResponse)
def create_task(todo_id : int , task : TaskCreate , db : Session = Depends(get_db))->TodoResponse:
    existing_todo = db.get(Todo,todo_id)
    if existing_todo:
        text = task.text
        new_task = Task(text=text,todo_id=existing_todo.id)
        db.add(new_task)
        db.commit()
        db.refresh(existing_todo)
        return existing_todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")


@app.patch("/api/todos/{todo_id}/tasks/{task_id}",response_model=TodoResponse)
def update_task(todo_id : int , task_id : int , task : TaskUpdate , db : Session = Depends(get_db))->TodoResponse:
    stmt = select(Task).where(
        Task.id == task_id,
        Task.todo_id == todo_id 
    )
    existing_task = db.scalar(stmt)
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
    
    db.commit()
    db.refresh(existing_task)
    return existing_task.todo
    

@app.delete("/api/todos/{todo_id}/tasks/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_task(todo_id : int , task_id : int , db : Session = Depends(get_db)) -> None:
    stmt = select(Task).where(
        Task.id == task_id,
        Task.todo_id == todo_id 
    )   
    existing_task = db.scalar(stmt)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    db.delete(existing_task)
    db.commit()
    return 

    
