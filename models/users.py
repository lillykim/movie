from typing import TYPE_CHECKING, List, Optional
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
# from models.events import Event

if TYPE_CHECKING:
    from models.movie import Movie

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(nullable=False, unique=True)
    password: str = Field(nullable=False)
    username: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    movies: Optional[List["Movie"]] = Relationship(back_populates="user")

class UserSignIn(SQLModel):
    email: EmailStr
    password: str   

class UserSignUp(SQLModel):
    email: EmailStr
    password: str
    username: str 