"""
Flask web interface for the LifeStepsAI todo application.

This module exposes the existing :class:`TodoManager` through a small,
server-rendered web application.  The web layer is intentionally thin: all
validation and business rules remain in the ``Task`` model and the manager so
the CLI, interactive UI, and web UI behave consistently.

Run the application with::

    python -m todo_app.web

or, when the package is installed::

    todo-web
"""

import os

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from todo_app.exceptions import InvalidTaskDataError, TaskNotFoundException
from todo_app.manager import TodoManager

SECRET_KEY_ENV_VAR = "SECRET_KEY"
DEFAULT_SECRET_KEY = "lifestepsai-dev-secret-key"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
VALID_STATUS_FILTERS = {"all", "pending", "completed"}


def create_app(manager: TodoManager | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        manager: Optional :class:`TodoManager` instance.  When omitted, a new
            in-memory manager is created.  Injecting a manager is useful for
            tests and keeps the web layer decoupled from storage details.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(SECRET_KEY_ENV_VAR, DEFAULT_SECRET_KEY)

    todo_manager = manager if manager is not None else TodoManager()

    @app.get("/")
    def index() -> str:
        """Render the task dashboard with an optional status filter."""
        status = request.args.get("status", "all")
        if status not in VALID_STATUS_FILTERS:
            flash("Invalid filter selected. Showing all tasks.", "warning")
            status = "all"

        all_tasks = todo_manager.list_tasks()
        tasks = todo_manager.list_tasks(status=status)
        completed_count = sum(1 for task in all_tasks if task.completed)

        return render_template(
            "index.html",
            tasks=tasks,
            current_status=status,
            total_count=len(all_tasks),
            pending_count=len(all_tasks) - completed_count,
            completed_count=completed_count,
        )

    @app.route("/add", methods=["GET", "POST"])
    def add_task() -> str | Response:
        """Show the add-task form and create a task on valid submission."""
        form_title = ""
        form_description = ""

        if request.method == "POST":
            form_title = request.form.get("title", "")
            form_description = request.form.get("description", "")

            try:
                task = todo_manager.add_task(
                    title=form_title,
                    description=form_description,
                )
            except InvalidTaskDataError as exc:
                flash(str(exc), "danger")
            else:
                flash(f'Task "{task.title}" was added successfully.', "success")
                return redirect(url_for("index"))

        return render_template(
            "add.html",
            form_title=form_title,
            form_description=form_description,
        )

    @app.route("/edit/<int:task_id>", methods=["GET", "POST"])
    def edit_task(task_id: int) -> str | Response:
        """Show the edit form and update a task on valid submission."""
        try:
            task = todo_manager.get_task(task_id)
        except TaskNotFoundException as exc:
            flash(str(exc), "danger")
            return redirect(url_for("index"))

        form_title = request.form.get("title", task.title)
        form_description = request.form.get("description", task.description)

        if request.method == "POST":
            try:
                todo_manager.update_task(
                    task_id=task_id,
                    title=form_title,
                    description=form_description,
                )
            except (InvalidTaskDataError, TaskNotFoundException) as exc:
                flash(str(exc), "danger")
            else:
                flash(
                    f'Task "{form_title.strip()}" was updated successfully.',
                    "success",
                )
                return redirect(url_for("index"))

        return render_template(
            "edit.html",
            task=task,
            form_title=form_title,
            form_description=form_description,
        )

    @app.post("/delete/<int:task_id>")
    def delete_task(task_id: int) -> Response:
        """Delete a task and redirect back to the dashboard."""
        try:
            task = todo_manager.get_task(task_id)
            todo_manager.delete_task(task_id)
        except TaskNotFoundException as exc:
            flash(str(exc), "danger")
        else:
            flash(f'Task "{task.title}" was deleted.', "success")

        return redirect(url_for("index"))

    @app.post("/complete/<int:task_id>")
    def complete_task(task_id: int) -> Response:
        """Mark a task as complete and redirect back to the dashboard."""
        try:
            todo_manager.mark_complete(task_id)
        except TaskNotFoundException as exc:
            flash(str(exc), "danger")
        else:
            flash("Task marked as complete.", "success")

        return redirect(url_for("index"))

    @app.post("/incomplete/<int:task_id>")
    def incomplete_task(task_id: int) -> Response:
        """Mark a task as incomplete and redirect back to the dashboard."""
        try:
            todo_manager.mark_incomplete(task_id)
        except TaskNotFoundException as exc:
            flash(str(exc), "danger")
        else:
            flash("Task marked as incomplete.", "info")

        return redirect(url_for("index"))

    return app


def main() -> None:
    """Run the web application using environment-based host and port settings."""
    app = create_app()
    host = os.environ.get("HOST", DEFAULT_HOST)
    port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
