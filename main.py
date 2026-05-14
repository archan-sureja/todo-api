from fastapi import FastAPI 
from database import init_db 
from contextlib import asynccontextmanager
from routers import todos , tasks 

@asynccontextmanager
async def lifespan(app : FastAPI):
    await init_db()
    yield 
    print("shutting down fastapi application") 

app = FastAPI(lifespan=lifespan)

app.include_router(todos.router,prefix="/api/todos",tags=["todos"])
app.include_router(tasks.router,prefix="/api/todos/{todo_id}/tasks",tags=["tasks"])


    
