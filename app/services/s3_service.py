import io
import uuid

import aioboto3
from PIL import Image

from app.core.config import settings


class S3Service:
    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
        self.access_key = settings.S3_ACCESS_KEY_ID
        self.secret_key = settings.S3_SECRET_ACCESS_KEY
        self.region = settings.S3_REGION

    def _get_client_kwargs(self) -> dict:
        kwargs = {
            "service_name": "s3",
            "region_name": self.region,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    def optimize_image(self, file_bytes: bytes, max_size: int = 1200) -> tuple[bytes, str]:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img = img.convert("RGB")
            img.thumbnail((max_size, max_size))
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=85)
            return buffer.getvalue(), "image/webp"

    async def ensure_bucket_exists(self) -> None:
        async with self.session.client(**self._get_client_kwargs()) as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except Exception:
                try:
                    await client.create_bucket(Bucket=self.bucket_name)
                except Exception:
                    pass

    async def upload_image(self, file_bytes: bytes, content_type: str = "image/jpeg") -> str:
        await self.ensure_bucket_exists()
        optimized_bytes, new_content_type = self.optimize_image(file_bytes)
        file_key = f"scans/{uuid.uuid4().hex}.webp"

        async with self.session.client(**self._get_client_kwargs()) as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=optimized_bytes,
                ContentType=new_content_type,
            )

        if settings.S3_PUBLIC_DOMAIN:
            return f"{settings.S3_PUBLIC_DOMAIN.rstrip('/')}/{file_key}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"


s3_service = S3Service()
