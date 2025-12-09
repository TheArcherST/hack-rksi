import uuid
from pathlib import Path

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, UploadFile, File
from hack.core.providers import ConfigS3
from hack.rest_server.models import AuthorizedUser
from hack.rest_server.providers import S3Client
from hack.rest_server.schemas.files import UploadFileResponseDTO

router = APIRouter(
    prefix="/files",
)


def _build_public_url(config: ConfigS3, key: str) -> str:
    base = config.public_base_url or (
        f"{config.endpoint_url.rstrip('/')}/{config.bucket}"
    )
    return f"{base}/{key}"


@router.post(
    "",
    response_model=UploadFileResponseDTO,
    status_code=201,
)
@inject
async def upload_event_image(
        s3_client: FromDishka[S3Client],
        s3_config: FromDishka[ConfigS3],
        # user, because profiles uploading might be implemented in the future
        _authorized_user: FromDishka[AuthorizedUser],
        file: UploadFile = File(...),
) -> UploadFileResponseDTO:
    ext = Path(file.filename or "").suffix
    key = f"events/{uuid.uuid4()}{ext}"
    content_type = file.content_type or "application/octet-stream"
    body = await file.read()
    await s3_client.put_object(
        Bucket=s3_config.bucket,
        Key=key,
        Body=body,
        ACL="public-read",
        ContentType=content_type,
    )
    url = _build_public_url(s3_config, key)
    return UploadFileResponseDTO(url=url)
