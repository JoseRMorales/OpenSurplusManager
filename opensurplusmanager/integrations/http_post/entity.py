from dataclasses import dataclass


@dataclass
class HTTPPostEntity:
    name: str
    path: str
    method: str
    body: str
    headers: dict
