"""Resource wrappers. Tests talk to these instead of building URLs themselves."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from api_client.client import APIClient, APIResponse


class Resource:
    path: str

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def list(self, **params: Any) -> APIResponse:
        return self.client.get(self.path, params=params)

    def get(self, resource_id: int | str) -> APIResponse:
        return self.client.get(f"{self.path}/{resource_id}")


class PostsResource(Resource):
    path = "/posts"

    def comments(self, post_id: int) -> APIResponse:
        return self.client.get(f"/posts/{post_id}/comments")

    def create(self, payload: Mapping[str, Any]) -> APIResponse:
        return self.client.post(self.path, json_body=dict(payload))

    def replace(self, post_id: int, payload: Mapping[str, Any]) -> APIResponse:
        return self.client.put(f"{self.path}/{post_id}", json_body=dict(payload))

    def update(self, post_id: int, payload: Mapping[str, Any]) -> APIResponse:
        return self.client.patch(f"{self.path}/{post_id}", json_body=dict(payload))

    def delete(self, post_id: int) -> APIResponse:
        return self.client.delete(f"{self.path}/{post_id}")


class CommentsResource(Resource):
    path = "/comments"


class UsersResource(Resource):
    path = "/users"

    def posts(self, user_id: int) -> APIResponse:
        return self.client.get(f"/users/{user_id}/posts")

    def albums(self, user_id: int) -> APIResponse:
        return self.client.get(f"/users/{user_id}/albums")

    def todos(self, user_id: int) -> APIResponse:
        return self.client.get(f"/users/{user_id}/todos")


class TodosResource(Resource):
    path = "/todos"


class AlbumsResource(Resource):
    path = "/albums"
