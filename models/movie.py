from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.users import User

class Movie(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="영화 고유 번호 (자동 증가)")
    
    user_id: int = Field(foreign_key="user.id", nullable=False, description="등록자 (회원 id, 외래키)")

    title: str = Field(max_length=255, nullable=False, description="영화 제목")
    story: str = Field(max_length=255, nullable=False, description="영화 줄거리")
    actors: str = Field(max_length=255, nullable=False, description="영화 배우")
    poster_path: Optional[str] = Field(default=None, max_length=255, description="포스터 이미지 파일명")
    rating: Optional[float] = Field(default=None, description="평균 별점")

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="등록 일시")
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, description="수정 일시")

    user: "User" = Relationship(back_populates="movies")
