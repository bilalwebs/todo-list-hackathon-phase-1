#!/usr/bin/env python3
"""
Demo script showing LifeStepsAI Todo Application functionality.
"""

import sys

sys.path.insert(0, '/mnt/d/hackathon-robotic/todo-list/src')

from todo_app import TodoManager


def print_separator():
    print("\n" + "=" * 70)

def demo():
    """Run a comprehensive demo of all features."""
    print("\n🚀 LifeStepsAI Todo Application - Phase I Demo")
    print("   In-Memory Python Console App")
    print_separator()

    # Initialize manager
    manager = TodoManager()
    print("\n✅ TodoManager initialized")

    # Demo 1: Add tasks
    print_separator()
    print("\n📝 DEMO 1: Adding Tasks")
    print("-" * 70)

    task1 = manager.add_task(title="Buy groceries", description="Milk, eggs, bread")
    print(f"✅ Added: {task1}")

    task2 = manager.add_task(
        title="Team meeting", description="Discuss Q1 roadmap at 2 PM"
    )
    print(f"✅ Added: {task2}")

    task3 = manager.add_task(title="Write documentation")
    print(f"✅ Added: {task3}")

    # Demo 2: View all tasks
    print_separator()
    print("\n👀 DEMO 2: Viewing All Tasks")
    print("-" * 70)

    all_tasks = manager.list_tasks(status="all")
    print(f"\nTotal tasks: {len(all_tasks)}")
    for task in all_tasks:
        status = "✓" if task.completed else "☐"
        print(f"  {status} [{task.id}] {task.title}")
        if task.description:
            print(f"      → {task.description}")

    # Demo 3: Mark tasks complete
    print_separator()
    print("\n✅ DEMO 3: Marking Tasks Complete")
    print("-" * 70)

    manager.mark_complete(task_id=1)
    print(f"✅ Marked task {task1.id} as complete")

    manager.mark_complete(task_id=2)
    print(f"✅ Marked task {task2.id} as complete")

    # Demo 4: View by status
    print_separator()
    print("\n📊 DEMO 4: Viewing Tasks by Status")
    print("-" * 70)

    completed = manager.list_tasks(status="completed")
    pending = manager.list_tasks(status="pending")

    print(f"\n✓ Completed tasks ({len(completed)}):")
    for task in completed:
        print(f"  [{task.id}] {task.title}")

    print(f"\n☐ Pending tasks ({len(pending)}):")
    for task in pending:
        print(f"  [{task.id}] {task.title}")

    # Demo 5: Update task
    print_separator()
    print("\n✏️  DEMO 5: Updating a Task")
    print("-" * 70)

    print(f"\nBefore: {task3.title}")
    manager.update_task(
        task_id=task3.id,
        title="Write comprehensive documentation",
        description="Include setup guide, examples, and API reference"
    )
    updated_task = manager.get_task(task3.id)
    print(f"After:  {updated_task.title}")
    print(f"        {updated_task.description}")

    # Demo 6: Delete task
    print_separator()
    print("\n🗑️  DEMO 6: Deleting a Task")
    print("-" * 70)

    print(f"\nDeleting task {task2.id}: '{task2.title}'")
    manager.delete_task(task_id=task2.id)
    print("✅ Task deleted successfully")

    remaining = manager.list_tasks()
    print(f"\nRemaining tasks: {len(remaining)}")
    for task in remaining:
        status = "✓" if task.completed else "☐"
        print(f"  {status} [{task.id}] {task.title}")

    # Demo 7: Toggle completion
    print_separator()
    print("\n🔄 DEMO 7: Toggling Task Completion")
    print("-" * 70)

    task4 = manager.add_task(title="Review code", description="Check PRs")
    print(f"\nNew task: {task4} (Status: {'✓' if task4.completed else '☐'})")

    manager.toggle_complete(task_id=task4.id)
    task4 = manager.get_task(task4.id)
    print(f"After toggle 1: (Status: {'✓' if task4.completed else '☐'})")

    manager.toggle_complete(task_id=task4.id)
    task4 = manager.get_task(task4.id)
    print(f"After toggle 2: (Status: {'✓' if task4.completed else '☐'})")

    # Final summary
    print_separator()
    print("\n📊 FINAL SUMMARY")
    print("-" * 70)

    all_tasks = manager.list_tasks()
    completed_count = len([t for t in all_tasks if t.completed])
    pending_count = len([t for t in all_tasks if not t.completed])

    print(f"\nTotal tasks: {len(all_tasks)}")
    print(f"Completed: {completed_count}")
    print(f"Pending: {pending_count}")

    print("\nAll tasks:")
    for task in all_tasks:
        status = "✓" if task.completed else "☐"
        print(f"  {status} [{task.id}] {task.title}")

    print_separator()
    print("\n✅ Demo completed successfully!")
    print("   All features working as expected.\n")

if __name__ == "__main__":
    demo()
