from sqlmodel import Session, select

from app.models.task import Task
from app.schemas.task import TaskCreate


def get_user_tasks(user_id: int, session: Session) -> list[Task]:
    return session.exec(select(Task).where(Task.user_id == user_id)).all()


def create_task(task: TaskCreate, user_id: int, session: Session) -> Task:
    task = Task.model_validate(task)
    task.user_id = user_id
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_tasks(task_ids: list[int], user_id: int, session: Session) -> list[Task]:
    return session.exec(
        select(Task).where(Task.id.in_(task_ids), Task.user_id == user_id)
    ).all()
