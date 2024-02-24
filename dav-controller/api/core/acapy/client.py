import json
import os
import time
import yaml

from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pymongo.database import Database
from pydantic import BaseModel
from typing import List, Optional, Union
from uuid import UUID

import requests
import structlog

from ...db.session import COLLECTION_NAMES
from ..config import settings
from .config import AgentConfig, MultiTenantAcapy, SingleTenantAcapy
from .models import CreatePresentationResponse, WalletDid

_client = None
logger = structlog.getLogger(__name__)

WALLET_DID_URI = "/wallet/did"
PUBLIC_WALLET_DID_URI = "/wallet/did/public"
CREATE_PRESENTATION_REQUEST_URL = "/present-proof/create-request"
PRESENT_PROOF_RECORDS = "/present-proof/records"


class PresExProofConfig(BaseModel):
    pres_exch_id: str
    proof_req_config_id: str

    class Config:
        allow_population_by_field_name = True


class AcapyClient:
    acapy_host = settings.ACAPY_ADMIN_URL
    service_endpoint = settings.ACAPY_AGENT_URL

    wallet_token: Optional[str] = None
    agent_config: AgentConfig

    def __init__(self, db: Database = None):
        if settings.ACAPY_TENANCY == "multi":
            self.agent_config = MultiTenantAcapy()
        elif settings.ACAPY_TENANCY == "single":
            self.agent_config = SingleTenantAcapy()
        else:
            logger.warning("ACAPY_TENANCY not set, assuming SingleTenantAcapy")
            self.agent_config = SingleTenantAcapy()

        if _client:
            return _client
        self.format_args_function_map = {
            "$threshold_date_19": self.get_threshold_birthdate_19,
            "$now": self.get_now,
        }
        self._db = db
        super().__init__()

    def get_threshold_birthdate_19(self) -> int:
        d = datetime.today()
        birth_date = datetime(d.year - 19, d.month, d.day)
        birth_date_format = "%Y%m%d"
        return int(birth_date.strftime(birth_date_format))

    def get_now(self) -> int:
        return int(time.time())

    def update_proof_req_dict(self, proof_req_dict: dict) -> dict:
        for k, v in proof_req_dict.items():
            if isinstance(v, dict):
                self.update_proof_req_dict(v)
            elif isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        self.update_proof_req_dict(i)
            elif v in list(self.format_args_function_map.keys()):
                proof_req_dict[k] = self.format_args_function_map[v]()
        return proof_req_dict

    def generate_verification_proof_request(
        self,
        proof_config_ident: str = "age-verification-bc-person-crdential",
    ):
        proof_req_dict = None
        with open("/app/api/proof_config.yaml", "r") as stream:
            config_dict = yaml.safe_load(stream)
            try:
                proof_req_dict = config_dict[proof_config_ident]["proof-request"]
            except KeyError:
                raise ValueError(
                    f"Could not find proof request for {proof_config_ident}"
                )
        proof_req_dict = self.update_proof_req_dict(proof_req_dict)
        req_attr_dict = {}
        for i, req_attr in enumerate(proof_req_dict["requested_attributes"]):
            label = os.environ.get("REQ_ATTR_LABEL_PREFIX", "req_attr_") + str(i)
            req_attr_dict[label] = req_attr
        proof_req_dict["requested_attributes"] = req_attr_dict
        req_pred_dict = {}
        for i, req_pred in enumerate(proof_req_dict["requested_predicates"]):
            label = os.environ.get("REQ_PRED_LABEL_PREFIX", "req_pred_") + str(i)
            req_pred_dict[label] = req_pred
        proof_req_dict["requested_predicates"] = req_pred_dict
        logger.error(f"--- {proof_req_dict} ---") 
        return proof_req_dict

    def create_presentation_request(
        self,
        proof_config_ident: str = "age-verification-bc-person-crdential",
        presentation_request_configuration: dict = None,
    ) -> CreatePresentationResponse:
        logger.debug(">>> create_presentation_request")
        if presentation_request_configuration:
            present_proof_payload = {
                "proof_request": presentation_request_configuration
            }
        else:
            present_proof_payload = {
                "proof_request": self.generate_verification_proof_request(
                    proof_config_ident=proof_config_ident
                )
            }

        resp_raw = requests.post(
            self.acapy_host + CREATE_PRESENTATION_REQUEST_URL,
            headers=self.agent_config.get_headers(),
            json=present_proof_payload,
        )

        # TODO: Determine if this should assert it received a json object
        assert resp_raw.status_code == 200, resp_raw.content

        resp = json.loads(resp_raw.content)
        result = CreatePresentationResponse.parse_obj(resp)

        logger.debug("<<< create_presenation_request")
        pres_ex_id = result.presentation_exchange_id
        col = self._db.get_collection(
            COLLECTION_NAMES.PRES_EX_ID_TO_PROOF_REQ_CONFIG_ID
        )
        proof_ex_req_config_id = PresExProofConfig(
            pres_exch_id=pres_ex_id, proof_req_config_id=proof_config_ident
        )
        db_result = col.insert_one(jsonable_encoder(proof_ex_req_config_id))
        return result

    def get_presentation_request(self, presentation_exchange_id: Union[UUID, str]):
        logger.debug(">>> get_presentation_request")

        resp_raw = requests.get(
            self.acapy_host
            + PRESENT_PROOF_RECORDS
            + "/"
            + str(presentation_exchange_id),
            headers=self.agent_config.get_headers(),
        )

        # TODO: Determine if this should assert it received a json object
        assert resp_raw.status_code == 200, resp_raw.content

        resp = json.loads(resp_raw.content)

        logger.debug(f"<<< get_presentation_request -> {resp}")
        return resp

    def verify_presentation(self, presentation_exchange_id: Union[UUID, str]):
        logger.debug(">>> verify_presentation")

        resp_raw = requests.post(
            self.acapy_host
            + PRESENT_PROOF_RECORDS
            + "/"
            + str(presentation_exchange_id)
            + "/verify-presentation",
            headers=self.agent_config.get_headers(),
        )
        assert resp_raw.status_code == 200, resp_raw.content

        resp = json.loads(resp_raw.content)

        logger.debug(f"<<< verify_presentation -> {resp}")
        return resp

    def get_wallet_did(self, public=False) -> WalletDid:
        logger.debug(">>> get_wallet_did")
        url = None
        if public:
            url = self.acapy_host + PUBLIC_WALLET_DID_URI
        else:
            url = self.acapy_host + WALLET_DID_URI

        resp_raw = requests.get(
            url,
            headers=self.agent_config.get_headers(),
        )

        # TODO: Determine if this should assert it received a json object
        assert (
            resp_raw.status_code == 200
        ), f"{resp_raw.status_code}::{resp_raw.content}"

        resp = json.loads(resp_raw.content)

        if public:
            resp_payload = resp["result"]
        else:
            resp_payload = resp["results"][0]

        did = WalletDid.parse_obj(resp_payload)

        logger.debug(f"<<< get_wallet_did -> {did}")
        return did
