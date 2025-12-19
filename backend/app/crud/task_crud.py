from sqlmodel import Session, select

from app.models.task import Task
from app.schemas.task import TaskCreate


def get_user_tasks(user_id: int, session: Session) -> list[Task]:
    return list(session.exec(select(Task).where(Task.user_id == user_id)).all())


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

def get_tasks(task_ids: list[int], user_id: int, session: Session) -> list[Task]:
    if not task_ids:
        return []
    return list(session.exec(
        select(Task)
        .where(Task.id.in_(task_ids))  # type: ignore[union-attr]
        .where(Task.user_id == user_id)
    ).all())
