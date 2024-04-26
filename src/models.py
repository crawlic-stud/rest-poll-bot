from pydantic import BaseModel


class LocationPolls(BaseModel):
    where: str = ""
    polls: list["Poll"]


class Poll(BaseModel):
    name: str
    chat_id: int
    message_id: int
