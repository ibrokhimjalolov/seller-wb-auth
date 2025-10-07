from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """Модель пользователя Wildberries"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, comment="ID пользователя")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания записи")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Дата обновления записи")

    # Связь с куками
    cookies = relationship("Cookie", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id})>"


class Cookie(Base):
    """Модель куки для авторизации"""
    __tablename__ = "cookies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="ID пользователя")
    name = Column(String(255), nullable=False, comment="Название куки")
    value = Column(Text, nullable=False, comment="Значение куки")
    expire_date = Column(DateTime(timezone=True), nullable=True, comment="Дата истечения куки")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания записи")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Дата обновления записи")

    # Связь с пользователем
    user = relationship("User", back_populates="cookies")

    def __repr__(self):
        return f"<Cookie(id={self.id}, name='{self.name}', user_id={self.user_id})>"
