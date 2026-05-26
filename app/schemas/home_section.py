from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class HomeSectionBase(BaseModel):
    key: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class HomeSectionCreate(HomeSectionBase):
    pass


class HomeSectionUpdate(BaseModel):
    key: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class HomeSectionOut(BaseModel):
    id: int
    key: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class HomeContentSectionOut(BaseModel):
    id: Optional[int] = None
    key: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)