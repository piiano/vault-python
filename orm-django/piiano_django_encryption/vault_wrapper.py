import contextvars
import enum
import logging
from typing import Any, Dict, List, Optional

import requests


class Reason(enum.Enum):
    AppFunctionality = "AppFunctionality"
    Analytics = "Analytics"
    Notifications = "Notifications"
    Marketing = "Marketing"
    ThirdPartyMarketing = "ThirdPartyMarketing"
    FraudPreventionSecurityAndCompliance = "FraudPreventionSecurityAndCompliance"
    AccountManagement = "AccountManagement"
    Maintenance = "Maintenance"
    DataSubjectRequest = "DataSubjectRequest"
    # Other = "Other"
    # TODO: Support other_reason field

    @classmethod
    def values(cls):
        return [e.value for e in cls]


class EncryptionType(enum.Enum):
    randomized = "randomized"
    deterministic = "deterministic"


class VaultException(Exception):
    pass


class Vault:
    def __init__(self, vault_url: str, auth_token: str, default_collection: str):
        self.auth_token = auth_token
        self.vault_url = vault_url
        self.default_collection = default_collection
        self._session: contextvars.ContextVar[
            Optional[requests.Session]] = contextvars.ContextVar('vault_session', default=None)

        # a mapping between (collection, field_name) to transformation name
        self._transformations: contextvars.ContextVar[Optional[Dict[tuple[str, str], str]]] = contextvars.ContextVar(
            'vault_transformations', default=None)

        self._reason: contextvars.ContextVar[Optional[Reason]] = contextvars.ContextVar('vault_reason', default=None)

    def _init_session(self) -> requests.Session:
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        }
        session.headers.update(headers)
        self._session.set(session)
        return session

    def _init_transformations(self) -> Dict:
        transformations: Dict[tuple[str, str], str] = {}
        self._transformations.set(transformations)
        return transformations

    def _get_transformations(self):
        transformations = self._transformations.get()
        if transformations is None:
            transformations = self._init_transformations()
        return transformations

    def make_request(self, method: str, url: str, **kwargs):
        session = self._session.get()
        if session is None:
            session = self._init_session()
        try:
            response = session.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            raise VaultException(f"Request failed: {e}")
        # self.log.append(LogLine(method, url, kwargs, response))
        return response

    def encrypt(
            self,
            plaintext: str,
            field_name: str,
            *,
            reason: Optional[Reason],
            collection: Optional[str],
            encryption_type: Optional[EncryptionType] = None,
            expiration_secs: Optional[int] = None) -> str:

        print("ENCRYPT", plaintext, field_name, reason, collection, encryption_type, expiration_secs)
        if reason is None:
            reason = self._reason.get()
        if reason is None:
            reason = Reason.AppFunctionality
        query_params: Dict[str, Any] = {"reason": reason.value}
        if expiration_secs:
            query_params["expiration_secs"] = expiration_secs
        post_body: List[Dict[str, Any]] = [{"object": {"fields": {field_name: plaintext}}}]
        if encryption_type:
            post_body[0]['type'] = encryption_type.value
        response = self.make_request(
            "POST",
            f"{self.vault_url}/api/pvlt/1.0/data/collections/{collection}/encrypt/objects",
            params=query_params,
            json=post_body)
        if response.status_code != 200:
            raise VaultException(f"Failed to encrypt: {response}, {response.text}")
        return response.json()[0]["ciphertext"]

    def decrypt(self, ciphertext: str, field_name: str, reason: Optional[Reason], collection: Optional[str]) -> str:
        transformations = self._get_transformations()
        if (collection, field_name) in transformations:
            field_name = f'{field_name}.{transformations[(collection, field_name)]}'
        print("DECRYPT", ciphertext, field_name, reason, collection)
        if reason is None:
            reason = self._reason.get()
        if reason is None:
            reason = Reason.AppFunctionality
        response = self.make_request(
            "POST",
            f"{self.vault_url}/api/pvlt/1.0/data/collections/{collection}/decrypt/objects",
            params={"reason": reason.value},
            json=[{"encrypted_object": {"ciphertext": ciphertext}, "props": [field_name]}])
        print(response.status_code, response.json())
        if response.status_code != 200:
            raise VaultException(f"Failed to decrypt: {response}, {response.text}")
        return response.json()[0]["fields"][field_name]

    def bulk_decrypt(self, cipertexts: List[str], field_name: str, reason: Optional[Reason], collection: Optional[str]) -> List[str]:
        print("BULK_DECRYPT", cipertexts, field_name, reason, collection)
        if reason is None:
            reason = self._reason.get()
        if reason is None:
            reason = Reason.AppFunctionality
        response = self.make_request(
            "POST",
            f"{self.vault_url}/api/pvlt/1.0/data/collections/{collection}/decrypt/objects",
            params={"reason": reason.value},
            json=[{"encrypted_object": {"ciphertext": ciphertext}, "props": [field_name]} for ciphertext in cipertexts])
        print(response.status_code, response.json())
        if response.status_code != 200:
            raise VaultException(f"Failed to decrypt: {response}, {response.text}")
        return [r["fields"][field_name] for r in response.json()]

    def add_collection(self, collection: str, collection_type: str, properties: List[Dict]):
        url = f"{self.vault_url}/api/pvlt/1.0/ctl/collections/"
        fields = dict(
            name=collection,
            type=collection_type,
            properties=properties,
        )
        response = self.make_request("POST", url, json=fields)
        if response.status_code != 200:
            raise VaultException(f"Failed to add collection: {response}, {response.text}")

    def remove_collection(self, collection: str):
        url = f"{self.vault_url}/api/pvlt/1.0/ctl/collections/{collection}"
        response = self.make_request("DELETE", url)
        if response.status_code != 200:
            raise VaultException(f"Failed to remove collection: {response}, {response.text}")

    def add_property(self, property_name: str, collection: str, description: str, is_encrypted: bool, is_index: bool, is_nullable: bool, is_unique: bool, data_type_name: str):
        url = f"{self.vault_url}/api/pvlt/1.0/ctl/collections/{collection}/properties/{property_name}"
        fields = dict(
            description=description,
            is_encrypted=is_encrypted,
            is_index=is_index,
            is_nullable=is_nullable,
            is_unique=is_unique,
            data_type_name=data_type_name,
            name=property_name,
        )

        response = self.make_request("POST", url, json=fields)
        if response.status_code != 200:
            raise VaultException(f"Failed to add property: {response}, {response.text}")

    def remove_property(self, property_name: str, collection: str):
        url = f"{self.vault_url}/api/pvlt/1.0/ctl/collections/{collection}/properties/{property_name}"
        response = self.make_request("DELETE", url)
        if response.status_code != 200:
            raise VaultException(f"Failed to remove property: {response}, {response.text}")

    def add_transformation(self, field_name: str, collection_name: str, transformation_name: str):
        transformations = self._get_transformations()
        if (collection_name, field_name) in transformations:
            raise ValueError(
                f"Transformation already exists for {collection_name}.{field_name}: {transformations[(collection_name, field_name)]}")
        transformations[(collection_name, field_name)] = transformation_name

    def remove_transformation(self, field_name: str, collection_name: str):
        transformations = self._get_transformations()
        if (collection_name, field_name) not in transformations:
            raise ValueError(f"No transformation exists for {collection_name}.{field_name}")
        del transformations[(collection_name, field_name)]

    def mask(self, field_name: str, collection_name: str):
        self.add_transformation(field_name, collection_name, "mask")

    def remove_mask(self, field_name: str, collection_name: str):
        self.remove_transformation(field_name, collection_name)

    def add_reason(self, reason: Reason):
        self._reason.set(reason)

    def remove_reason(self):
        self._reason.set(None)
