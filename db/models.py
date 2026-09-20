from sqlalchemy import Table, Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Ассоциативная таблица для связи многие-ко-многим между users и candidates
# Используется Table() вместо класса, так как таблица не имеет дополнительных полей
favorites = Table("favorites", Base.metadata,
                  Column("user_vk_id", Integer,
                         ForeignKey("users.vk_id", ondelete="CASCADE"),
                         primary_key=True),
                  Column("candidate_vk_id", Integer,
                         ForeignKey("candidates.vk_id", ondelete="CASCADE"),
                         primary_key=True),
                  Index("idx_favorites_user", "user_vk_id")
                  )

class User(Base):
    __tablename__ = "users"

    vk_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    age = Column(Integer)
    city = Column(String(100))
    gender = Column(Integer)

    candidates = relationship("Candidate", secondary=favorites, back_populates="users")


class Candidate(Base):
    __tablename__ = "candidates"

    vk_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    profile_link = Column(String(255), nullable=False)

    photos = relationship("Photo", back_populates="candidate")
    users = relationship("User", secondary=favorites, back_populates="candidates")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_vk_id = Column(
        Integer,
        ForeignKey("candidates.vk_id", ondelete="CASCADE"),
        nullable=False
    )
    url = Column(String(255), nullable=False)
    likes_count = Column(Integer, default=0)

    candidate = relationship("Candidate", back_populates="photos")

    __table_args__ = (Index("idx_photos_candidate", "candidate_vk_id"),)
