"""Tests for the Flask web interface.

The web layer delegates all business rules to ``TodoManager`` and ``Task``.
These tests verify routing, template rendering, flash messages, and error
handling while keeping the manager as the single source of truth.
"""

import pytest
from flask.testing import FlaskClient

from todo_app.manager import TodoManager
from todo_app.web import create_app


@pytest.fixture
def manager() -> TodoManager:
    """Return a fresh in-memory manager for each test."""
    return TodoManager()


@pytest.fixture
def client(manager: TodoManager) -> FlaskClient:
    """Return a Flask test client bound to the shared manager."""
    app = create_app(manager)
    app.config.update(TESTING=True)
    return app.test_client()


def test_index_renders_empty_state(client: FlaskClient) -> None:
    """The dashboard renders an empty state when no tasks exist."""
    response = client.get("/")

    assert response.status_code == 200
    assert b"No tasks found" in response.data
    assert b"Add Task" in response.data


def test_index_displays_tasks_and_statistics(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The dashboard lists tasks and shows correct counters."""
    first = manager.add_task(title="Write report", description="Quarterly report")
    second = manager.add_task(title="Send email")
    manager.mark_complete(second.id)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Write report" in response.data
    assert b"Send email" in response.data
    assert first.completed is False
    assert b"Total" in response.data
    assert b"Pending" in response.data
    assert b"Completed" in response.data


def test_index_filters_pending_tasks(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The pending filter hides completed tasks."""
    manager.add_task(title="Pending task")
    completed = manager.add_task(title="Completed task")
    manager.mark_complete(completed.id)

    response = client.get("/?status=pending")

    assert response.status_code == 200
    assert b"Pending task" in response.data
    assert b"Completed task" not in response.data


def test_index_filters_completed_tasks(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The completed filter hides pending tasks."""
    manager.add_task(title="Pending task")
    completed = manager.add_task(title="Completed task")
    manager.mark_complete(completed.id)

    response = client.get("/?status=completed")

    assert response.status_code == 200
    assert b"Completed task" in response.data
    assert b"Pending task" not in response.data


def test_index_invalid_filter_falls_back_to_all(
    client: FlaskClient, manager: TodoManager
) -> None:
    """An unknown filter displays a warning and shows all tasks."""
    manager.add_task(title="Visible task")

    response = client.get("/?status=unknown", follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid filter selected" in response.data
    assert b"Visible task" in response.data


def test_add_page_renders_form(client: FlaskClient) -> None:
    """The add page renders the task form."""
    response = client.get("/add")

    assert response.status_code == 200
    assert b"Add a New Task" in response.data
    assert b'name="title"' in response.data
    assert b'name="description"' in response.data


def test_add_task_creates_task_and_redirects(
    client: FlaskClient, manager: TodoManager
) -> None:
    """Submitting valid data creates a task and shows a success message."""
    response = client.post(
        "/add",
        data={"title": "  Buy milk  ", "description": "Two litres"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was added successfully" in response.data
    assert b"Buy milk" in response.data

    task = manager.get_task(1)
    assert task.title == "Buy milk"
    assert task.description == "Two litres"


def test_add_task_with_empty_title_shows_error(
    client: FlaskClient, manager: TodoManager
) -> None:
    """Invalid input is rejected by the Task validation and reported."""
    response = client.post(
        "/add",
        data={"title": "   ", "description": "No title"},
    )

    assert response.status_code == 200
    assert b"Title cannot be empty" in response.data
    assert len(manager.list_tasks()) == 0
    assert b"No title" in response.data


def test_edit_page_renders_current_values(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The edit page is pre-filled with the current task values."""
    task = manager.add_task(title="Old title", description="Old description")

    response = client.get(f"/edit/{task.id}")

    assert response.status_code == 200
    assert b"Old title" in response.data
    assert b"Old description" in response.data


def test_edit_task_updates_values(
    client: FlaskClient, manager: TodoManager
) -> None:
    """Submitting valid data updates the task."""
    task = manager.add_task(title="Old title", description="Old description")

    response = client.post(
        f"/edit/{task.id}",
        data={"title": "New title", "description": "New description"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"was updated successfully" in response.data

    updated = manager.get_task(task.id)
    assert updated.title == "New title"
    assert updated.description == "New description"


def test_edit_task_with_invalid_title_shows_error(
    client: FlaskClient, manager: TodoManager
) -> None:
    """Invalid updates are rejected and the original task is preserved."""
    task = manager.add_task(title="Original title")

    response = client.post(
        f"/edit/{task.id}",
        data={"title": "", "description": ""},
    )

    assert response.status_code == 200
    assert b"Title cannot be empty" in response.data
    assert manager.get_task(task.id).title == "Original title"


def test_edit_missing_task_redirects_with_error(client: FlaskClient) -> None:
    """Editing a missing task redirects to the dashboard with an error."""
    response = client.get("/edit/999", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task with ID 999 not found" in response.data


def test_delete_task_removes_it(
    client: FlaskClient, manager: TodoManager
) -> None:
    """Deleting a task removes it and shows a success message."""
    task = manager.add_task(title="Delete me")

    response = client.post(f"/delete/{task.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"was deleted" in response.data
    assert len(manager.list_tasks()) == 0


def test_delete_missing_task_shows_error(client: FlaskClient) -> None:
    """Deleting a missing task shows a not-found message."""
    response = client.post("/delete/999", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task with ID 999 not found" in response.data


def test_complete_task_marks_it_complete(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The complete route marks a task as complete."""
    task = manager.add_task(title="Finish me")

    response = client.post(f"/complete/{task.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task marked as complete" in response.data
    assert manager.get_task(task.id).completed is True


def test_complete_missing_task_shows_error(client: FlaskClient) -> None:
    """Completing a missing task shows a not-found message."""
    response = client.post("/complete/999", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task with ID 999 not found" in response.data


def test_incomplete_task_marks_it_pending(
    client: FlaskClient, manager: TodoManager
) -> None:
    """The incomplete route marks a completed task as pending."""
    task = manager.add_task(title="Reopen me")
    manager.mark_complete(task.id)

    response = client.post(f"/incomplete/{task.id}", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task marked as incomplete" in response.data
    assert manager.get_task(task.id).completed is False


def test_incomplete_missing_task_shows_error(client: FlaskClient) -> None:
    """Marking a missing task incomplete shows a not-found message."""
    response = client.post("/incomplete/999", follow_redirects=True)

    assert response.status_code == 200
    assert b"Task with ID 999 not found" in response.data
