import json
from typing import Any
from uuid import UUID

from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.exceptions import ExternalStorageError, StorageConnectionError


class S3Backend(StorageBackend):
    def __init__(self, url: str, endpoint_url: str | None = None) -> None:
        super().__init__(url)
        self._session: Any = None
        self._client: Any = None
        self._client_context: Any = None
        self._bucket: str = ""
        self._key_prefix: str = ""
        self._endpoint_url = endpoint_url
        self._parse_url()

    def _parse_url(self) -> None:
        from urllib.parse import urlparse

        parsed = urlparse(self._url)
        self._bucket = parsed.netloc
        self._key_prefix = parsed.path.lstrip("/")

    async def connect(self) -> None:
        if self._client is not None:
            return

        try:
            from aiobotocore.session import get_session
        except ImportError as e:
            raise StorageConnectionError(
                "aiobotocore is not installed. Install with: pip install pydantic-toast[s3]",
                url=self._url,
                cause=e,
            ) from e

        try:
            self._session = get_session()
            client_kwargs: dict[str, Any] = {}
            if self._endpoint_url:
                client_kwargs["endpoint_url"] = self._endpoint_url

            self._client_context = self._session.create_client("s3", **client_kwargs)
            self._client = await self._client_context.__aenter__()

            await self._client.head_bucket(Bucket=self._bucket)
        except Exception as e:
            if self._client_context is not None:
                try:
                    await self._client_context.__aexit__(None, None, None)
                except Exception:
                    pass
                self._client = None
                self._client_context = None

            error_msg = str(e)
            if "NoSuchBucket" in error_msg or "404" in error_msg:
                raise StorageConnectionError(
                    f"S3 bucket '{self._bucket}' does not exist",
                    url=self._url,
                    cause=e,
                ) from e
            raise StorageConnectionError(
                f"Failed to connect to S3: {e}",
                url=self._url,
                cause=e,
            ) from e

    async def disconnect(self) -> None:
        if self._client_context is not None:
            await self._client_context.__aexit__(None, None, None)
            self._client = None
            self._client_context = None
            self._session = None

    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        if self._client is None:
            raise StorageConnectionError("Not connected to S3", url=self._url)

        try:
            key = self._make_key(id, class_name)
            body = json.dumps(data)
            await self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType="application/json",
            )
        except Exception as e:
            raise ExternalStorageError(f"Failed to save record: {e}") from e

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        if self._client is None:
            raise StorageConnectionError("Not connected to S3", url=self._url)

        try:
            key = self._make_key(id, class_name)
            response = await self._client.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                body = await stream.read()
            result: dict[str, Any] = json.loads(body.decode("utf-8"))
            return result
        except Exception as e:
            error_str = str(e)
            if "NoSuchKey" in error_str or "404" in error_str:
                return None
            raise ExternalStorageError(f"Failed to load record: {e}") from e

    def _make_key(self, id: UUID, class_name: str) -> str:
        if self._key_prefix:
            return f"{self._key_prefix}/{class_name}/{id}.json"
        return f"{class_name}/{id}.json"
