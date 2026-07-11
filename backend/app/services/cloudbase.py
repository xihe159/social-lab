from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any


class CloudBaseError(RuntimeError):
    pass


class CloudBaseClient:
    def __init__(self) -> None:
        self.env_id = os.getenv("CLOUDBASE_ENV_ID", "").strip()
        self.region = os.getenv("CLOUDBASE_REGION", "ap-shanghai").strip()
        self.server_api_key = os.getenv("CLOUDBASE_SERVER_API_KEY", "").strip()

        if not self.env_id or not self.server_api_key:
            raise CloudBaseError(
                "CloudBase 服务端环境变量未配置，请设置 CLOUDBASE_ENV_ID 和 CLOUDBASE_SERVER_API_KEY。"
            )

        self.base_url = (
            f"https://{self.env_id}.api.tcloudbasegateway.com/v1/database/"
            "instances/(default)/databases/(default)/collections"
        )

    def add_document(self, collection: str, data: dict[str, Any]) -> str | None:
        payload = self._request(
            "POST",
            self._documents_url(collection),
            {"data": [data]},
        )
        data_block = payload.get("data") or {}
        ids = data_block.get("insertedIds") or data_block.get("ids") or []
        return data_block.get("_id") or data_block.get("id") or (ids[0] if ids else None)

    def query_documents(
        self,
        collection: str,
        query: dict[str, Any],
        *,
        order: list[dict[str, str]] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "query": json.dumps(query, ensure_ascii=False),
            "limit": str(limit),
            "offset": str(offset),
        }
        if order:
            params["order"] = json.dumps(order, ensure_ascii=False)

        payload = self._request("GET", self._documents_url(collection, params=params))
        return (payload.get("data") or {}).get("list") or []

    def get_document(self, collection: str, document_id: str) -> dict[str, Any] | None:
        items = self.query_documents(collection, {"_id": document_id}, limit=1)
        return items[0] if items else None

    def update_document(
        self,
        collection: str,
        query: dict[str, Any],
        data: dict[str, Any],
        *,
        multi: bool = False,
        upsert: bool = False,
        replace: bool = False,
    ) -> int:
        body: dict[str, Any] = {
            "query": query,
            "data": data if replace else {"$set": data},
            "multi": multi,
            "upsert": upsert,
            "replaceMode": replace,
        }
        payload = self._request("PATCH", self._documents_url(collection), body)
        return int((payload.get("data") or {}).get("updated") or 0)

    def remove_documents(
        self,
        collection: str,
        query: dict[str, Any],
        *,
        multi: bool = True,
    ) -> int:
        payload = self._request(
            "POST",
            f"{self._documents_url(collection)}/remove",
            {"query": query, "multi": multi},
        )
        return int((payload.get("data") or {}).get("deleted") or 0)

    def _documents_url(
        self,
        collection: str,
        *,
        params: dict[str, str] | None = None,
    ) -> str:
        url = f"{self.base_url}/{urllib.parse.quote(collection)}/documents"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        return url

    def _request(
        self,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        encoded_body = (
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        )
        request = urllib.request.Request(
            url,
            data=encoded_body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.server_api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept-Language": "zh-CN",
                "X-TCB-Region": self.region,
                "X-Request-Id": str(uuid.uuid4()),
                "X-SDK-Version": "social-lab-render/0.1",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CloudBaseError(
                f"CloudBase 请求失败：HTTP {exc.code} {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise CloudBaseError(f"CloudBase 网络请求失败：{exc.reason}") from exc

        payload = json.loads(raw) if raw else {}
        if payload.get("code") and payload.get("code") not in {"SUCCESS", "NORMAL"}:
            raise CloudBaseError(
                f"CloudBase 返回错误：{payload.get('code')} {payload.get('message')}"
            )
        return payload


_client: CloudBaseClient | None = None


def get_cloudbase_client() -> CloudBaseClient:
    global _client
    if _client is None:
        _client = CloudBaseClient()
    return _client
