#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
=================================================
作者：[郭磊]
手机：[15210720528]
Email：[174000902@qq.com]
Github：https://github.com/guolei19850528/py3_wisharetec
=================================================
"""
import hashlib
import json
from datetime import timedelta
from typing import Union

import diskcache
import redis
import requests
from addict import Dict
from jsonschema.validators import Draft202012Validator
from requests import Response


class Admin(object):
    def __init__(
            self,
            base_url: str = "https://sq.wisharetec.com/",
            username: str = None,
            password: str = None,
            cache: Union[diskcache.Cache, redis.Redis, redis.StrictRedis] = None
    ):
        base_url = base_url if isinstance(base_url, str) else "https://sq.wisharetec.com/"
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.username = username if isinstance(username, str) else ""
        self.password = password if isinstance(password, str) else ""
        self.cache = cache if isinstance(cache, (diskcache.Cache, redis.Redis, redis.StrictRedis)) else None
        self.token: dict = {}

    def _default_response_handler(self, response: Response = None):
        """
        default response handler
        :param response: requests.Response instance
        :return:
        """
        if isinstance(response, Response) and response.status_code == 200:
            json_addict = Dict(response.json())
            if Draft202012Validator({
                "type": "object",
                "properties": {
                    "status": {
                        "oneOf": [
                            {"type": "integer", "const": 100},
                            {"type": "string", "const": "100"},
                        ]
                    }
                },
                "required": ["status"],
            }).is_valid(json_addict):
                return json_addict.data, response
        return False, response

    def check_login(
            self,
            method: str = "GET",
            url: str = "/old/serverUserAction!checkSession.action",
            **kwargs
    ):
        method = method if isinstance(method, str) else "GET"
        url = url if isinstance(url, str) else "/old/serverUserAction!checkSession.action"
        if not url.startswith("http"):
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"{self.base_url}{url}"
        headers = kwargs.get("headers", {})
        headers.setdefault("Token", self.token.get("token"))
        headers.setdefault("Companycode", self.token.get("companyCode"))
        kwargs["headers"] = headers
        response = requests.request(method, url, **kwargs)
        if isinstance(response, Response) and response.status_code == 200:
            return response.text.strip() == "null", response
        return False, response

    def login_with_cache(
            self,
            expire: Union[float, int, timedelta] = None,
            login_kwargs: dict = None,
            check_login_kwargs: dict = None
    ):
        """
        login with cache
        :param expire: expire time default 7100 seconds
        :param login_kwargs: self.login kwargs
        :param check_login_kwargs: self.check_login kwargs
        :return:
        """
        login_kwargs = login_kwargs if isinstance(login_kwargs, dict) else {}
        check_login_kwargs = check_login_kwargs if isinstance(check_login_kwargs, dict) else {}
        cache_key = f"py3_wisharetec_token_{self.username}"
        if isinstance(self.cache, diskcache.Cache):
            self.token = self.cache.get(cache_key)
        if isinstance(self.cache, (redis.Redis, redis.StrictRedis)):
            self.token = json.loads(self.cache.get(cache_key))
        self.token = self.token if isinstance(self.token, dict) else {}
        state, _ = self.check_login(**check_login_kwargs)
        if not state:
            self.login(**login_kwargs)
            if isinstance(self.token, dict) and len(self.token.keys()):
                if isinstance(self.cache, diskcache.Cache):
                    self.cache.set(
                        key=cache_key,
                        value=self.token,
                        expire=expire or timedelta(days=60).total_seconds()
                    )
                if isinstance(self.cache, (redis.Redis, redis.StrictRedis)):
                    self.cache.setex(
                        name=cache_key,
                        value=json.dumps(self.token),
                        time=expire or timedelta(days=60),
                    )

        return self

    def login(
            self,
            method: str = "POST",
            url: str = "/manage/login",
            **kwargs
    ):
        method = method if isinstance(method, str) else "POST"
        url = url if isinstance(url, str) else "/manage/login"
        if not url.startswith("http"):
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"{self.base_url}{url}"
        data = kwargs.get("data", {})
        data.setdefault("username", self.username)
        data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        data.setdefault("mode", "PASSWORD")
        kwargs["data"] = data
        response = requests.request(method=method, url=url, **kwargs)
        result, _ = self._default_response_handler(response)
        if Draft202012Validator({
            "type": "object",
            "properties": {
                "token": {"type": "string", "minLength": 1},
                "companyCode": {"type": "string", "minLength": 1},
            },
            "required": ["token", "companyCode"],
        }).is_valid(result):
            self.token = result
        return self

    def request_with_token(
            self, method: str = "GET",
            url: str = None,
            **kwargs
    ):
        """
        request with token
        :param method: requests.request method
        :param url: requests.request url
        :param kwargs: requests.request kwargs
        :return:
        """
        method = method if isinstance(method, str) else "GET"
        url = url if isinstance(url, str) else ""
        if not url.startswith("http"):
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"{self.base_url}{url}"
        headers = kwargs.get("headers", {})
        headers.setdefault("Token", self.token.get("token"))
        headers.setdefault("Companycode", self.token.get("companyCode"))
        kwargs["headers"] = headers
        response = requests.request(method, url, **kwargs)
        return self._default_response_handler(response)

    def download_export(
            self,
            export_id: Union[int, str] = None,
            save_path: str = None,
            query_export_with_paginator_kwargs: dict = None,
            retry_kwargs: dict = None,
    ):
        pass
