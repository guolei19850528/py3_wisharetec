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
import py3_requests
import redis
import requests
from addict import Dict
from jsonschema.validators import Draft202012Validator
from requests import Response
from retrying import retry


class RequestUrl:
    BASE_URL: str = "https://sq.wisharetec.com/"
    LOGIN_URL: str = "/manage/login"
    QUERY_LOGIN_STATE_URL: str = "/old/serverUserAction!checkSession.action"
    QUERY_COMMUNITY_WITH_PAGINATOR_URL: str = "/manage/communityInfo/getAdminCommunityList"
    QUERY_COMMUNITY_DETAIL_URL: str = "/manage/communityInfo/getCommunityInfo"
    QUERY_ROOM_WITH_PAGINATOR_URL: str = "/manage/communityRoom/listCommunityRoom"
    QUERY_ROOM_DETAIL_URL: str = "/manage/communityRoom/getFullRoomInfo"
    QUERY_ROOM_EXPORT_URL: str = "/manage/communityRoom/exportDelayCommunityRoomList"
    QUERY_REGISTER_USER_WITH_PAGINATOR_URL: str = "/manage/user/register/list"
    QUERY_REGISTER_USER_DETAIL_URL: str = "/manage/user/register/detail"
    QUERY_REGISTER_USER_EXPORT_URL: str = "/manage/user/register/list/export"
    QUERY_REGISTER_OWNER_WITH_PAGINATOR_URL: str = "/manage/user/information/register/list"
    QUERY_REGISTER_OWNER_DETAIL_URL: str = "/manage/user/information/register/detail"
    QUERY_REGISTER_OWNER_EXPORT_URL: str = "/manage/user/information/register/list/export"
    QUERY_UNREGISTER_OWNER_WITH_PAGINATOR_URL: str = "/manage/user/information/unregister/list"
    QUERY_UNREGISTER_OWNER_DETAIL_URL: str = "/manage/user/information/unregister/detail"
    QUERY_UNREGISTER_OWNER_EXPORT_URL: str = "/manage/user/information/unregister/list/export"
    QUERY_SHOP_GOODS_CATEGORY_WITH_PAGINATOR_URL: str = "/manage/productCategory/getProductCategoryList"
    QUERY_SHOP_GOODS_WITH_PAGINATOR_URL: str = "/manage/shopGoods/getAdminShopGoods"
    QUERY_SHOP_GOODS_DETAIL_URL: str = "/manage/shopGoods/getShopGoodsDetail"
    SAVE_SHOP_GOODS_URL: str = "/manage/shopGoods/saveSysShopGoods"
    UPDATE_SHOP_GOODS_URL: str = "/manage/shopGoods/updateShopGoods"
    QUERY_SHOP_GOODS_PUSH_TO_STORE_URL: str = "/manage/shopGoods/getGoodsStoreEdits"
    SAVE_SHOP_GOODS_PUSH_TO_STORE_URL: str = "/manage/shopGoods/saveGoodsStoreEdits"
    QUERY_STORE_PRODUCT_WITH_PAGINATOR_URL: str = "/manage/storeProduct/getAdminStoreProductList"
    QUERY_STORE_PRODUCT_DETAIL_URL: str = "/manage/storeProduct/getStoreProductInfo"
    UPDATE_STORE_PRODUCT_URL: str = "/manage/storeProduct/updateStoreProductInfo"
    UPDATE_STORE_PRODUCT_STATUS_URL: str = "/manage/storeProduct/updateProductStatus"
    QUERY_BUSINESS_ORDER_WITH_PAGINATOR_URL: str = "/manage/businessOrderShu/list"
    QUERY_BUSINESS_ORDER_DETAIL_URL: str = "/manage/businessOrderShu/view"
    QUERY_BUSINESS_ORDER_EXPORT_1_URL: str = "/manage/businessOrder/exportToExcelByOrder"
    QUERY_BUSINESS_ORDER_EXPORT_2_URL: str = "/manage/businessOrder/exportToExcelByProduct"
    QUERY_BUSINESS_ORDER_EXPORT_3_URL: str = "/manage/businessOrder/exportToExcelByOrderAndProduct"
    QUERY_WORK_ORDER_WITH_PAGINATOR_URL: str = "/old/orderAction!viewList.action"
    QUERY_WORK_ORDER_DETAIL_URL: str = "/old/orderAction!view.action"
    QUERY_WORK_ORDER_EXPORT_URL: str = "/manage/order/work/export"
    QUERY_PARKING_AUTH_WITH_PAGINATOR_URL: str = "/manage/carParkApplication/carParkCard/list"
    QUERY_PARKING_AUTH_DETAIL_URL: str = "/manage/carParkApplication/carParkCard"
    UPDATE_PARKING_AUTH_URL: str = "/manage/carParkApplication/carParkCard"
    QUERY_PARKING_AUTH_AUDIT_WITH_PAGINATOR_URL: str = "/manage/carParkApplication/carParkCard/parkingCardManagerByAudit"
    QUERY_PARKING_AUTH_AUDIT_CHECK_WITH_PAGINATOR_URL: str = "/manage/carParkApplication/getParkingCheckList"
    UPDATE_PARKING_AUTH_AUDIT_STATUS_URL: str = "/manage/carParkApplication/completeTask"
    QUERY_EXPORT_WITH_PAGINATOR_URL: str = "/manage/export/log"
    UPLOAD_URL: str = "/upload"


class ValidatorJsonSchema:
    """
    json schema settings
    """
    NORMAL_SCHEMA = {
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
    }

    LOGIN_SCHEMA = {
        "type": "object",
        "properties": {
            "token": {"type": "string", "minLength": 1},
            "companyCode": {"type": "string", "minLength": 1},
        },
        "required": ["token", "companyCode"],
    }

    RESULTLIST_SCHEMA = {
        'type': 'object',
        'properties': {
            "resultList": {"type": "array"},
        },
        "required": ["resultList"]
    }


class ResponseHandler:
    """
    response handler
    """

    @staticmethod
    def normal_handler(response: Response = None):
        if isinstance(response, Response) and response.status_code == 200:
            json_addict = Dict(response.json())
            if Draft202012Validator(ValidatorJsonSchema.NORMAL_SCHEMA).is_valid(instance=json_addict):
                return json_addict.get("data", Dict())
            return None
        raise Exception(f"Response Handler Error {response.status_code}|{response.text}")

    @staticmethod
    def resultlist_handler(response: Response = None):
        result = ResponseHandler.normal_handler(response=response)
        if Draft202012Validator(ValidatorJsonSchema.RESULTLIST_SCHEMA).is_valid(instance=result):
            return result.get("resultList", [])
        return []


class Admin(object):
    def __init__(
            self,
            base_url: str = RequestUrl.BASE_URL,
            username: str = "",
            password: str = "",
            cache: Union[diskcache.Cache, redis.Redis, redis.StrictRedis] = None
    ):
        self.base_url = base_url[:-1] if isinstance(base_url, str) and base_url.endswith("/") else base_url
        self.username = username
        self.password = password
        self.cache = cache
        self.token: dict = {}

    def query_login_state(
            self,
            **kwargs
    ):
        """
        query login state
        :param kwargs:
        :return:
        """
        kwargs = Dict(kwargs)
        kwargs.setdefault("method", "POST")
        kwargs.setdefault(
            "response_handler",
            lambda x: isinstance(x, Response) and x.status_code == 200 and x.text.strip() == "null"
        )
        kwargs.setdefault("url", f"{RequestUrl.QUERY_LOGIN_STATE_URL}")
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("headers", Dict({}))
        kwargs.headers.setdefault("Token", self.token.get("token", ""))
        kwargs.headers.setdefault("Companycode", self.token.get("companyCode", ""))
        return py3_requests.request(**kwargs.to_dict())

    def login_with_cache(
            self,
            expire: Union[float, int, timedelta] = None,
            login_kwargs: dict = {},
            query_login_state_kwargs: dict = {}
    ):
        """
        login with cache
        :param expire: expire time default 7100 seconds
        :param login_kwargs: self.login kwargs
        :param query_login_state_kwargs: self.query_login_state kwargs
        :return:
        """
        cache_key = f"py3_wisharetec_token_{self.username}"
        if isinstance(self.cache, diskcache.Cache):
            self.token = self.cache.get(cache_key)
        if isinstance(self.cache, (redis.Redis, redis.StrictRedis)):
            self.token = json.loads(self.cache.get(cache_key))
        self.token = self.token if isinstance(self.token, dict) else {}
        if not self.query_login_state(**query_login_state_kwargs):
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
            **kwargs
    ):
        """
        login
        :param kwargs:
        :return:
        """
        kwargs = Dict(kwargs)
        kwargs.setdefault("method", "POST")
        kwargs.setdefault("response_handler", ResponseHandler.normal_handler)
        kwargs.setdefault("url", f"{RequestUrl.LOGIN_URL}")
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("data", Dict())
        kwargs.data.setdefault("username", self.username)
        kwargs.data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        kwargs.data.setdefault("mode", "PASSWORD")
        result = py3_requests.request(**kwargs.to_dict())
        if Draft202012Validator(ValidatorJsonSchema.LOGIN_SCHEMA).is_valid(result):
            self.token = result
        return self

    def request_with_token(
            self,
            **kwargs
    ):
        """
        request with token
        :param kwargs: requests.request kwargs
        :return:
        """
        kwargs = Dict(kwargs)
        kwargs.setdefault("method", "GET")
        kwargs.setdefault("response_handler", ResponseHandler.normal_handler)
        kwargs.setdefault("url", f"")
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("headers", Dict({}))
        kwargs.headers.setdefault("Token", self.token.get("token", ""))
        kwargs.headers.setdefault("Companycode", self.token.get("companyCode", ""))
        return py3_requests.request(**kwargs.to_dict())
