from fastapi import FastAPI , status
from fastapi.exceptions import HTTPException
from schemas.todo import TodoCreateUpdate, Todo , TaskCreate, Task, TaskUpdate
todo_store : dict[int,Todo] = {}
app = FastAPI()

@app.post("/api/todos")
def create_todo(todo : TodoCreateUpdate):
    new_id = max(k for k in todo_store.keys()) + 1 if todo_store else 1
    todo_obj = Todo(
        id = new_id,
        title=todo.title,
    ) 
    todo_store[new_id] = todo_obj
    return todo_obj 

@app.get("/api/todos")
def list_todo() -> list[Todo]:
    return todo_store.values()

@app.get("/api/todos/{todo_id}")
def get_todo(todo_id : int) -> Todo:
    for k in todo_store:
        if k== todo_id:
            return todo_store[k] 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id : int, todo : TodoCreateUpdate) -> Todo:
    for k in todo_store:
        if k==todo_id:
            todo_store[k]["title"] = todo.title 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.delete("/api/todos/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id : int) -> None:
    res = todo_store.pop(todo_id,None)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")
    return  

@app.post("/api/todos/{todo_id}/tasks")
def create_task(todo_id : int , task : TaskCreate):
    if todo_id in todo_store : 
        new_task_id = max(
            id for task.id in todo_store[todo_id].tasks  
        ) + 1 if todo_store[todo_id].tasks else 1 
        new_task = Task(
            id = new_task_id ,
            text=TaskCreate['text']
        )
        todo_store[todo_id].tasks.append(new_task)
        return todo_store[todo_id]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.patch("/api/todos/{todo_id}/tasks/{task_id}")
def update_task(todo_id : int , task_id : int , task : TaskUpdate):
    current_task = None 
    if todo_id in todo_store:
        for t in todo_store[todo_id]:
            if t['id'] == task_id:
                current_task = t 
        if current_task:
            if task.text is not None:
                current_task['text'] = task.text
            if task.status is not None:
                current_task['status'] = task.status 
            return todo_store[todo_id]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task does not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")

@app.delete("/api/todos/{todo_id}/tasks/{task_id}")
def delete_task(todo_id : int , task_id : int) -> None: 
    if todo_id in todo_store:
        for t in todo_store[todo_id]:
            if t['id'] == task_id:
                todo_store[todo_id].tasks.remove(t)
                return 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Task does not found")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo list does not found")
