from jinja2.nodes import Test
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker


from main import app, get_db
from database import Base


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)


async def override_get_db():
    async with TestingSessionLocal() as db:
        yield db



app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    with TestClient(app) as test_client:
        yield test_client

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


class TestTodoEndpoints:
    """Test cases for Todo CRUD endpoints"""

    def test_create_todo(self, client):
        """Test creating a new todo"""
        response = client.post(
            "/api/todos",
            json={"title": "Buy groceries"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert "id" in data
        assert "created_at" in data
        assert data["tasks"] == []

    def test_create_todo_invalid_title(self, client):
        """Test creating todo with invalid title"""
        response = client.post(
            "/api/todos",
            json={"title": ""}
        )
        assert response.status_code == 422

    def test_create_todo_title_too_long(self, client):
        """Test creating todo with title exceeding max length"""
        response = client.post(
            "/api/todos",
            json={"title": "x" * 101}
        )
        assert response.status_code == 422

    def test_list_todos_empty(self, client):
        """Test listing todos when empty"""
        response = client.get("/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_todos_with_multiple_items(self, client):
        """Test listing multiple todos"""
        # Create multiple todos
        for i in range(3):
            client.post(
                "/api/todos",
                json={"title": f"Todo {i + 1}"}
            )

        response = client.get("/api/todos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Todo 1"
        assert data[1]["title"] == "Todo 2"
        assert data[2]["title"] == "Todo 3"

    def test_get_todo_success(self, client):
        """Test getting a specific todo"""
        create_response = client.post(
            "/api/todos",
            json={"title": "Test Todo"}
        )
        todo_id = create_response.json()["id"]

        response = client.get(f"/api/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"

    def test_get_todo_not_found(self, client):
        """Test getting a non-existent todo"""
        response = client.get("/api/todos/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo list does not found"

    def test_update_todo_success(self, client):
        """Test updating a todo"""
        create_response = client.post(
            "/api/todos",
            json={"title": "Original Title"}
        )
        todo_id = create_response.json()["id"]

        response = client.patch(
            f"/api/todos/{todo_id}",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["id"] == todo_id

    def test_update_todo_not_found(self, client):
        """Test updating a non-existent todo"""
        response = client.patch(
            "/api/todos/999",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo list does not found"

    def test_update_todo_invalid_title(self, client):
        """Test updating todo with invalid title"""
        create_response = client.post(
            "/api/todos",
            json={"title": "Original Title"}
        )
        todo_id = create_response.json()["id"]

        response = client.patch(
            f"/api/todos/{todo_id}",
            json={"title": ""}
        )
        assert response.status_code == 422

    def test_delete_todo_success(self, client):
        """Test deleting a todo"""
        create_response = client.post(
            "/api/todos",
            json={"title": "Todo to delete"}
        )
        todo_id = create_response.json()["id"]

        response = client.delete(f"/api/todos/{todo_id}")
        assert response.status_code == 204

        # Verify todo is deleted
        get_response = client.get(f"/api/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client):
        """Test deleting a non-existent todo"""
        response = client.delete("/api/todos/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo list does not found"


class TestTaskEndpoints:
    """Test cases for Task CRUD endpoints"""

    def test_create_task_success(self, client):
        """Test creating a task for a todo"""
        # Create a todo first
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        # Create a task
        response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["text"] == "Buy milk"
        assert data["tasks"][0]["completed"] is False

    def test_create_task_todo_not_found(self, client):
        """Test creating a task for non-existent todo"""
        response = client.post(
            "/api/todos/999/tasks",
            json={"text": "Buy milk"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Todo list does not found"

    def test_create_task_invalid_text(self, client):
        """Test creating task with invalid text"""
        # Create a todo first
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": ""}
        )
        assert response.status_code == 422

    def test_create_multiple_tasks(self, client):
        """Test creating multiple tasks for a todo"""
        # Create a todo
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        # Create multiple tasks
        for i in range(3):
            client.post(
                f"/api/todos/{todo_id}/tasks",
                json={"text": f"Item {i + 1}"}
            )

        # Verify all tasks are created
        response = client.get(f"/api/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 3

    def test_update_task_success(self, client):
        """Test updating a task"""
        # Create a todo and task
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        task_response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Update task
        response = client.patch(
            f"/api/todos/{todo_id}/tasks/{task_id}",
            json={"text": "Buy 2L milk", "completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"][0]["text"] == "Buy 2L milk"
        assert data["tasks"][0]["completed"] is True

    def test_update_task_only_text(self, client):
        """Test updating only task text"""
        # Create a todo and task
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        task_response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Update only text
        response = client.patch(
            f"/api/todos/{todo_id}/tasks/{task_id}",
            json={"text": "Buy almond milk"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"][0]["text"] == "Buy almond milk"
        assert data["tasks"][0]["completed"] is False

    def test_update_task_only_completed(self, client):
        """Test updating only task completed status"""
        # Create a todo and task
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        task_response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Update only completed status
        response = client.patch(
            f"/api/todos/{todo_id}/tasks/{task_id}",
            json={"completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"][0]["text"] == "Buy milk"
        assert data["tasks"][0]["completed"] is True

    def test_update_task_no_fields(self, client):
        """Test updating task with no fields provided"""
        # Create a todo and task
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        task_response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Try to update with no fields
        response = client.patch(
            f"/api/todos/{todo_id}/tasks/{task_id}",
            json={}
        )
        assert response.status_code == 400
        assert "No fields for updation is provided" in response.json()["detail"]

    def test_update_task_not_found(self, client):
        """Test updating non-existent task"""
        # Create a todo
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        response = client.patch(
            f"/api/todos/{todo_id}/tasks/999",
            json={"text": "Updated text"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_update_task_wrong_todo(self, client):
        """Test updating task with wrong todo_id"""
        # Create two todos and one task
        todo1_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo1_id = todo1_response.json()["id"]

        todo2_response = client.post(
            "/api/todos",
            json={"title": "Work"}
        )
        todo2_id = todo2_response.json()["id"]

        # Create task in todo1
        task_response = client.post(
            f"/api/todos/{todo1_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Try to update with wrong todo_id
        response = client.patch(
            f"/api/todos/{todo2_id}/tasks/{task_id}",
            json={"text": "Updated"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_delete_task_success(self, client):
        """Test deleting a task"""
        # Create a todo and task
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        task_response = client.post(
            f"/api/todos/{todo_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Delete task
        response = client.delete(f"/api/todos/{todo_id}/tasks/{task_id}")
        assert response.status_code == 204

        # Verify task is deleted
        todo_response = client.get(f"/api/todos/{todo_id}")
        assert len(todo_response.json()["tasks"]) == 0

    def test_delete_task_not_found(self, client):
        """Test deleting non-existent task"""
        # Create a todo
        todo_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo_id = todo_response.json()["id"]

        response = client.delete(f"/api/todos/{todo_id}/tasks/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_delete_task_wrong_todo(self, client):
        """Test deleting task with wrong todo_id"""
        # Create two todos and one task
        todo1_response = client.post(
            "/api/todos",
            json={"title": "Shopping"}
        )
        todo1_id = todo1_response.json()["id"]

        todo2_response = client.post(
            "/api/todos",
            json={"title": "Work"}
        )
        todo2_id = todo2_response.json()["id"]

        # Create task in todo1
        task_response = client.post(
            f"/api/todos/{todo1_id}/tasks",
            json={"text": "Buy milk"}
        )
        task_id = task_response.json()["tasks"][0]["id"]

        # Try to delete with wrong todo_id
        response = client.delete(f"/api/todos/{todo2_id}/tasks/{task_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"
