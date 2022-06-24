import flask_discord
from flask_discord import types
from requests_oauthlib import OAuth2Session


class CustomDiscordOAuth2Session(flask_discord.DiscordOAuth2Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scope = ["identify"]

    def create_session(
            self, scope: list = None, *, data: dict = None, prompt: bool = True,
            permissions: types.Permissions | int = 0, **params
    ):
        return super().create_session(self.scope, data=data, prompt=prompt, permissions=permissions, **params)

    def _make_session(self, token: str = None, state: str = None, scope: list = None) -> OAuth2Session:
        return super()._make_session(token=token, state=state, scope=self.scope)
