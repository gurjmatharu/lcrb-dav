import base64
import io
from typing import cast
import uuid
from datetime import datetime
from urllib.parse import urlencode

import qrcode
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as http_status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from jinja2 import Template
from pymongo.database import Database
from pyop.exceptions import InvalidAuthenticationRequest

from ..authSessions.crud import AuthSessionCreate, AuthSessionCRUD
from ..authSessions.models import AuthSessionPatch, AuthSessionState
from ..core.acapy.client import AcapyClient
from ..core.config import settings
from ..core.logger_util import log_debug
from ..db.session import get_db

# Access to the websocket
from ..routers.socketio import connections_reload, sio
from ..routers.webhook_deliverer import deliver_notification

# This allows the templates to insert assets like css, js or svg.
from ..templates.helpers import add_asset

logger: structlog.typing.FilteringBoundLogger = structlog.getLogger(__name__)

router = APIRouter()


@log_debug
@router.get(f"/age-verification/{{pid}}")
async def get_dav_request(pid: str, db: Database = Depends(get_db)):
    """Called by authorize webpage to see if request is verified."""
    auth_session = await AuthSessionCRUD(db).get(pid)

    pid = str(auth_session.id)
    connections = connections_reload()
    sid = connections.get(pid)

    """
     Check if proof is expired. But only if the proof has not been started.
     NOTE: This should eventually be moved to a background task.
    """
    if (
        auth_session.expired_timestamp < datetime.now()
        and auth_session.proof_status == AuthSessionState.INITIATED
    ):
        logger.info("PROOF EXPIRED")
        auth_session.proof_status = AuthSessionState.EXPIRED
        await AuthSessionCRUD(db).patch(
            str(auth_session.id), AuthSessionPatch(**auth_session.dict())
        )
        # Send message through the websocket.
        await sio.emit("status", {"status": "expired"}, to=sid)
        if auth_session.notify_endpoint:
            deliver_notification(
                "status", {"status": "expired"}, auth_session.notify_endpoint
            )
    if auth_session.proof_status == AuthSessionState.SUCCESS:
        pres_exch = auth_session.presentation_exchange
        # Needs to be checked
        pic_b64_enc = pres_exch["presentation~attach"][0]["picture"]
    return {
        "proof_status": auth_session.proof_status,
        "verified_picture": pic_b64_enc,
        "id": str(auth_session.id),
        "notify_endpoint": auth_session.notify_endpoint,
        "metadata": auth_session.metadata,
    }


# HTMLResponse
@log_debug
@router.post("/age-verification", response_class=JSONResponse)
async def new_dav_request(request: Request, db: Database = Depends(get_db)):
    logger.debug(">>> new_dav_request")

    req_query_params = request.query_params._dict

    #  create proof for this request
    new_user_id = str(uuid.uuid4())

    # retrieve presentation_request config.
    client = AcapyClient()

    # Create presentation_request to show on screen
    response = client.create_presentation_request()

    new_auth_session = AuthSessionCreate(
        metadata=req_query_params["metadata"],
        pres_exch_id=response.presentation_exchange_id,
        presentation_exchange=response.dict(),
        notify_endpoint=req_query_params["notify_endpoint"],
    )

    # save AuthSession
    auth_session = await AuthSessionCRUD(db).create(new_auth_session)

    # QR CONTENTS
    controller_host = settings.CONTROLLER_URL
    url_to_message = (
        controller_host + "/url/pres_exch/" + str(auth_session.pres_exch_id)
    )

    return {
        "id": str(auth_session.id),
        "status": AuthSessionState.INITIATED,
        "url": url_to_message,
    }


@log_debug
@router.get("/", response_class=HTMLResponse)
async def render_new_dav_request(request: Request, db: Database = Depends(get_db)):
    logger.debug(">>> render new_dav_request HTML page")

    req_query_params = request.query_params._dict

    #  create proof for this request
    new_user_id = str(uuid.uuid4())

    # retrieve presentation_request config.
    client = AcapyClient()

    # Create presentation_request to show on screen
    response = client.create_presentation_request()

    new_auth_session = AuthSessionCreate(
        metadata=req_query_params["metadata"],
        pres_exch_id=response.presentation_exchange_id,
        presentation_exchange=response.dict(),
        notify_endpoint=req_query_params["notify_endpoint"],
    )

    # save AuthSession
    auth_session = await AuthSessionCRUD(db).create(new_auth_session)

    # QR CONTENTS
    controller_host = settings.CONTROLLER_URL
    url_to_message = (
        controller_host + "/url/pres_exch/" + str(auth_session.pres_exch_id)
    )
    # CREATE the image
    buff = io.BytesIO()
    qrcode.make(url_to_message).save(buff, format="PNG")
    image_contents = base64.b64encode(buff.getvalue()).decode("utf-8")

    # This is the payload to send to the template
    deep_link_proof_url = (
        f"bcwallet://aries_connection_invitation?{url_to_message.split('?')[1]}"
    )
    data = {
        "image_contents": image_contents,
        "url": url_to_message,
        "add_asset": add_asset,
        "pres_exch_id": auth_session.pres_exch_id,
        "pid": auth_session.id,
        "controller_host": controller_host,
        "deep_link_url": deep_link_proof_url,
    }

    # Prepare the template
    template_file = open("api/templates/verified_credentials.html", "r").read()
    template = Template(template_file)
    # Render and return the template
    return template.render(data)
