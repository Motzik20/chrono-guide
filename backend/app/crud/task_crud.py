import datetime as dt

from sqlmodel import Session, select

from app.models.task import Task
from app.schemas.task import TaskCreate, TasksDelete


def get_unscheduled_tasks(user_id: int, session: Session) -> list[Task]:
    return list(
        session.exec(
            select(Task).where(Task.user_id == user_id).where(Task.scheduled_at == None)
        ).all()
    )


def get_scheduled_tasks(user_id: int, session: Session) -> list[Task]:
    """Get tasks that are scheduled but not completed."""
    return list(
        session.exec(
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.scheduled_at != None)
            .where(Task.completed_at == None)
        ).all()
    )


def get_completed_tasks(user_id: int, session: Session) -> list[Task]:
    """Get tasks that are completed."""
    return list(
        session.exec(
            select(Task).where(Task.user_id == user_id).where(Task.completed_at != None)
        ).all()
    )


def get_tasks_by_ids(task_ids: list[int], user_id: int, session: Session) -> list[Task]:
    if not task_ids:
        return []
    return list(
        session.exec(
            select(Task)
            .where(Task.id.in_(task_ids))  # type: ignore[union-attr]
            .where(Task.user_id == user_id)
        ).all()
    )


def update_tasks_scheduled_at(
    task_scheduled: list[int],
    scheduled_at: dt.datetime,
    user_id: int,
    session: Session,
) -> None:
    """Update scheduled_at for multiple tasks. task_scheduled_times maps task_id to scheduled_at datetime."""
    if not task_scheduled:
        return

    for task_id in task_scheduled:
        task = session.exec(
            select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
        ).one()
        task.scheduled_at = scheduled_at
        session.add(task)
    session.flush()


def create_task(task: TaskCreate, user_id: int, session: Session) -> Task:
    task_model: Task = Task.model_validate(task)
    task_model.user_id = user_id
    session.add(task_model)
    session.flush()
    session.refresh(task_model)
    return task_model


def create_tasks(tasks: list[TaskCreate], user_id: int, session: Session) -> list[Task]:
    task_models: list[Task] = []
    for task in tasks:
        task_model: Task = Task.model_validate(task)
        task_model.user_id = user_id
        task_models.append(task_model)
    session.add_all(task_models)
    session.flush()
    for task_model in task_models:
        session.refresh(task_model)
    return task_models


def delete_task(task_id: int, user_id: int, session: Session) -> None:
    task = session.exec(
        select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
    ).one()
    session.delete(task)
    session.flush()


def delete_tasks(tasks_delete: TasksDelete, user_id: int, session: Session) -> None:
    for task_id in tasks_delete.task_ids:
        task = session.exec(
            select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
        ).one()
        session.delete(task)
    session.flush()
