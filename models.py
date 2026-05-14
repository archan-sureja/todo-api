from sqlalchemy import Column , Integer , String , Boolean , DateTime , ForeignKey
from sqlalchemy.orm import relationship , Mapped, mapped_column
from datetime import datetime,timezone 
from database import Base

class Task(Base):
    __tablename__ = "tasks"
    id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    text : Mapped[str] = mapped_column(String,nullable=False)
    completed : Mapped[bool]= mapped_column(Boolean,nullable=False,default=False)
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    todo_id : Mapped[int] = mapped_column(Integer,ForeignKey("todos.id"))
    todo : Mapped["Todo"] = relationship("Todo",back_populates="tasks",lazy="joined")

class Todo(Base):
    __tablename__ = "todos"
    id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    title : Mapped[str] = mapped_column(String,nullable=False)
    tasks : Mapped[list["Task"]] = relationship("Task",back_populates="todo",lazy="selectin")
    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )