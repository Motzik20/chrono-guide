from fastapi import Header


def get_current_user_id(x_user_id: int= Header(default=1)) -> int:
    return int(x_user_id)
