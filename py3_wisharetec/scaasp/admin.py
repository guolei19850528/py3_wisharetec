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
import pathlib
from datetime import timedelta, datetime
from typing import Union

import diskcache
import redis
import requests
from addict import Dict
from jsonschema.validators import Draft202012Validator
from requests import Response
from retrying import retry


class UrlSettings:
    LOGIN: str = "/manage/login"
    QUERY_LOGIN_STATE: str = "/old/serverUserAction!checkSession.action"
    QUERY_COMMUNITY_WITH_PAGINATOR: str = "/manage/communityInfo/getAdminCommunityList"
    QUERY_COMMUNITY_DETAIL: str = "/manage/communityInfo/getCommunityInfo"
    QUERY_ROOM_WITH_PAGINATOR: str = "/manage/communityRoom/listCommunityRoom"
    QUERY_ROOM_DETAIL: str = "/manage/communityRoom/getFullRoomInfo"
    QUERY_ROOM_EXPORT: str = "/manage/communityRoom/exportDelayCommunityRoomList"
    QUERY_REGISTER_USER_WITH_PAGINATOR: str = "/manage/user/register/list"
    QUERY_REGISTER_USER_DETAIL: str = "/manage/user/register/detail"
    QUERY_REGISTER_USER_EXPORT: str = "/manage/user/register/list/export"
    QUERY_REGISTER_OWNER_WITH_PAGINATOR: str = "/manage/user/information/register/list"
    QUERY_REGISTER_OWNER_DETAIL: str = "/manage/user/information/register/detail"
    QUERY_REGISTER_OWNER_EXPORT: str = "/manage/user/information/register/list/export"
    QUERY_UNREGISTER_OWNER_WITH_PAGINATOR: str = "/manage/user/information/unregister/list"
    QUERY_UNREGISTER_OWNER_DETAIL: str = "/manage/user/information/unregister/detail"
    QUERY_UNREGISTER_OWNER_EXPORT: str = "/manage/user/information/unregister/list/export"
    QUERY_SHOP_GOODS_CATEGORY_WITH_PAGINATOR: str = "/manage/productCategory/getProductCategoryList"
    QUERY_SHOP_GOODS_WITH_PAGINATOR: str = "/manage/shopGoods/getAdminShopGoods"
    QUERY_SHOP_GOODS_DETAIL: str = "/manage/shopGoods/getShopGoodsDetail"
    SAVE_SHOP_GOODS: str = "/manage/shopGoods/saveSysShopGoods"
    UPDATE_SHOP_GOODS: str = "/manage/shopGoods/updateShopGoods"
    QUERY_SHOP_GOODS_PUSH_TO_STORE: str = "/manage/shopGoods/getGoodsStoreEdits"
    SAVE_SHOP_GOODS_PUSH_TO_STORE: str = "/manage/shopGoods/saveGoodsStoreEdits"
    QUERY_STORE_PRODUCT_WITH_PAGINATOR: str = "/manage/storeProduct/getAdminStoreProductList"
    QUERY_STORE_PRODUCT_DETAIL: str = "/manage/storeProduct/getStoreProductInfo"
    UPDATE_STORE_PRODUCT: str = "/manage/storeProduct/updateStoreProductInfo"
    UPDATE_STORE_PRODUCT_STATUS: str = "/manage/storeProduct/updateProductStatus"
    QUERY_BUSINESS_ORDER_WITH_PAGINATOR: str = "/manage/businessOrderShu/list"
    QUERY_BUSINESS_ORDER_DETAIL: str = "/manage/businessOrderShu/view"
    QUERY_BUSINESS_ORDER_EXPORT_1: str = "/manage/businessOrder/exportToExcelByOrder"
    QUERY_BUSINESS_ORDER_EXPORT_2: str = "/manage/businessOrder/exportToExcelByProduct"
    QUERY_BUSINESS_ORDER_EXPORT_3: str = "/manage/businessOrder/exportToExcelByOrderAndProduct"
    QUERY_WORK_ORDER_WITH_PAGINATOR: str = "/old/orderAction!viewList.action"
    QUERY_WORK_ORDER_DETAIL: str = "/old/orderAction!view.action"
    QUERY_WORK_ORDER_EXPORT: str = "/manage/order/work/export"
    QUERY_PARKING_AUTH_WITH_PAGINATOR: str = "/manage/carParkApplication/carParkCard/list"
    QUERY_PARKING_AUTH_DETAIL: str = "/manage/carParkApplication/carParkCard"
    UPDATE_PARKING_AUTH: str = "/manage/carParkApplication/carParkCard"
    QUERY_PARKING_AUTH_AUDIT_WITH_PAGINATOR: str = "/manage/carParkApplication/carParkCard/parkingCardManagerByAudit"
    QUERY_PARKING_AUTH_AUDIT_CHECK_WITH_PAGINATOR: str = "/manage/carParkApplication/getParkingCheckList"
    UPDATE_PARKING_AUTH_AUDIT_STATUS: str = "/manage/carParkApplication/completeTask"
    QUERY_EXPORT_WITH_PAGINATOR: str = "/manage/export/log"
    UPLOAD: str = "/upload"


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

    def query_login_state(
            self,
            method: str = "GET",
            url: str = UrlSettings.QUERY_LOGIN_STATE,
            **kwargs
    ):
        method = method if isinstance(method, str) else "GET"
        url = url if isinstance(url, str) else UrlSettings.QUERY_LOGIN_STATE
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
            query_login_state_kwargs: dict = None
    ):
        """
        login with cache
        :param expire: expire time default 7100 seconds
        :param login_kwargs: self.login kwargs
        :param query_login_state_kwargs: self.query_login_state kwargs
        :return:
        """
        login_kwargs = login_kwargs if isinstance(login_kwargs, dict) else {}
        query_login_state_kwargs = query_login_state_kwargs if isinstance(query_login_state_kwargs, dict) else {}
        cache_key = f"py3_wisharetec_token_{self.username}"
        if isinstance(self.cache, diskcache.Cache):
            self.token = self.cache.get(cache_key)
        if isinstance(self.cache, (redis.Redis, redis.StrictRedis)):
            self.token = json.loads(self.cache.get(cache_key))
        self.token = self.token if isinstance(self.token, dict) else {}
        state, _ = self.query_login_state(**query_login_state_kwargs)
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
            url: str = UrlSettings.LOGIN,
            **kwargs
    ):
        method = method if isinstance(method, str) else "POST"
        url = url if isinstance(url, str) else UrlSettings.LOGIN
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
