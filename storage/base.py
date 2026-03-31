from abc import ABC, abstractmethod


class StorageClient(ABC):
    @abstractmethod
    def put_json(self, key: str, data: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_json(self, key: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def put_text(self, key: str, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_text(self, key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_keys(self, prefix: str) -> list[str]:
        raise NotImplementedError


def get_storage_client() -> StorageClient:
    from storage.minio_client import MinIOClient
    return MinIOClient()
