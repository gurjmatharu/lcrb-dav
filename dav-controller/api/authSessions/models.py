from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Dict, Optional

from api.core.acapy.client import AcapyClient
from api.core.models import UUIDModel
from pydantic import BaseModel, Field, validator

from ..core.config import settings


class AuthSessionState(StrEnum):
    INITIATED = auto()
    IN_PROGRESS = auto()
    SUCCESS = auto()
    FAILURE = auto()
    EXPIRED = auto()
    ABORTED = auto()


class AuthSessionBase(BaseModel):
    pres_exch_id: str
    expired_timestamp: datetime = Field(
        default=datetime.now()
        + timedelta(seconds=settings.CONTROLLER_PRESENTATION_EXPIRE_TIME)
    )
    metadata: Optional[dict] = None
    notify_endpoint: Optional[str] = None

    # @validator('metadata')
    # def prevent_dict_none(cls, v):
    #     assert v is not None, 'metadata may not be None'
    #     return v

    # @validator('notify_endpoint')
    # def prevent_str_none(cls, v):
    #     assert v is not None, 'notify_endpoint may not be None'
    #     return v

    class Config:
        allow_population_by_field_name = True


class AuthSession(AuthSessionBase, UUIDModel):
    proof_status: AuthSessionState = Field(default=AuthSessionState.INITIATED)

    @property
    def presentation_exchange(self) -> Dict:
        client = AcapyClient()
        return client.get_presentation_request(self.pres_exch_id)


class AuthSessionCreate(AuthSessionBase):
    pass


class AuthSessionPatch(AuthSessionBase):
    proof_status: AuthSessionState = Field(default=AuthSessionState.IN_PROGRESS)
    pass
