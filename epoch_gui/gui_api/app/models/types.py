from pydantic import BaseModel


class ListSitesRequest(BaseModel):
    client_id: str
