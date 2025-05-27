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


class RequestUrl(py3_requests.RequestUrl):
    BASE = "https://sq.wisharetec.com/"
    LOGIN = "/manage/login"
    QUERY_LOGIN_STATE = "/old/serverUserAction!checkSession.action"
    QUERY_COMMUNITY_WITH_PAGINATOR = "/manage/communityInfo/getAdminCommunityList"
    QUERY_COMMUNITY_DETAIL = "/manage/communityInfo/getCommunityInfo"
    QUERY_ROOM_WITH_PAGINATOR = "/manage/communityRoom/listCommunityRoom"
    QUERY_ROOM_DETAIL = "/manage/communityRoom/getFullRoomInfo"
    QUERY_ROOM_EXPORT = "/manage/communityRoom/exportDelayCommunityRoomList"
    QUERY_REGISTER_USER_WITH_PAGINATOR = "/manage/user/register/list"
    QUERY_REGISTER_USER_DETAIL = "/manage/user/register/detail"
    QUERY_REGISTER_USER_EXPORT = "/manage/user/register/list/export"
    QUERY_REGISTER_OWNER_WITH_PAGINATOR = "/manage/user/information/register/list"
    QUERY_REGISTER_OWNER_DETAIL = "/manage/user/information/register/detail"
    QUERY_REGISTER_OWNER_EXPORT = "/manage/user/information/register/list/export"
    QUERY_UNREGISTER_OWNER_WITH_PAGINATOR = "/manage/user/information/unregister/list"
    QUERY_UNREGISTER_OWNER_DETAIL = "/manage/user/information/unregister/detail"
    QUERY_UNREGISTER_OWNER_EXPORT = "/manage/user/information/unregister/list/export"
    QUERY_SHOP_GOODS_CATEGORY_WITH_PAGINATOR = "/manage/productCategory/getProductCategoryList"
    QUERY_SHOP_GOODS_WITH_PAGINATOR = "/manage/shopGoods/getAdminShopGoods"
    QUERY_SHOP_GOODS_DETAIL = "/manage/shopGoods/getShopGoodsDetail"
    SAVE_SHOP_GOODS = "/manage/shopGoods/saveSysShopGoods"
    UPDATE_SHOP_GOODS = "/manage/shopGoods/updateShopGoods"
    QUERY_SHOP_GOODS_PUSH_TO_STORE = "/manage/shopGoods/getGoodsStoreEdits"
    SAVE_SHOP_GOODS_PUSH_TO_STORE = "/manage/shopGoods/saveGoodsStoreEdits"
    QUERY_STORE_PRODUCT_WITH_PAGINATOR = "/manage/storeProduct/getAdminStoreProductList"
    QUERY_STORE_PRODUCT_DETAIL = "/manage/storeProduct/getStoreProductInfo"
    UPDATE_STORE_PRODUCT = "/manage/storeProduct/updateStoreProductInfo"
    UPDATE_STORE_PRODUCT_STATUS = "/manage/storeProduct/updateProductStatus"
    QUERY_BUSINESS_ORDER_WITH_PAGINATOR = "/manage/businessOrderShu/list"
    QUERY_BUSINESS_ORDER_DETAIL = "/manage/businessordershu/view"
    QUERY_BUSINESS_ORDER_EXPORT_1 = "/manage/businessOrder/exportToExcelByOrder"
    QUERY_BUSINESS_ORDER_EXPORT_2 = "/manage/businessOrder/exportToExcelByProduct"
    QUERY_BUSINESS_ORDER_EXPORT_3 = "/manage/businessOrder/exportToExcelByOrderAndProduct"
    QUERY_WORK_ORDER_WITH_PAGINATOR = "/old/orderAction!viewList.action"
    QUERY_WORK_ORDER_DETAIL = "/old/orderAction!view.action"
    QUERY_WORK_ORDER_EXPORT = "/manage/order/work/export"
    QUERY_PARKING_AUTH_WITH_PAGINATOR = "/manage/carParkApplication/carParkCard/list"
    QUERY_PARKING_AUTH_DETAIL = "/manage/carParkApplication/carParkCard"
    UPDATE_PARKING_AUTH = "/manage/carParkApplication/carParkCard"
    QUERY_PARKING_AUTH_AUDIT_WITH_PAGINATOR = "/manage/carParkApplication/carParkCard/parkingCardManagerByAudit"
    QUERY_PARKING_AUTH_AUDIT_CHECK_WITH_PAGINATOR = "/manage/carParkApplication/getParkingCheckList"
    UPDATE_PARKING_AUTH_AUDIT_STATUS = "/manage/carParkApplication/completeTask"
    QUERY_EXPORT_WITH_PAGINATOR = "/manage/export/log"
    UPLOAD = "/upload"
    QUERY_SURVEY_LIST_WITH_PAGINATOR="/manage/questionnaire/list/managen"
    QUERY_SURVEY_PARTICIPATION_LIST_WITH_PAGINATOR="/manage/questionnaire/joinuser/list"


class ValidatorJsonSchema(py3_requests.ValidatorJsonSchema):
    SUCCESS = Dict({
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
    })

    LOGIN = Dict({
        "type": "object",
        "properties": {
            "token": {"type": "string", "minLength": 1},
            "companyCode": {"type": "string", "minLength": 1},
        },
        "required": ["token", "companyCode"],
    })

    RESULTLIST = Dict({
        'type': 'object',
        'properties': {
            "resultList": {"type": "array"},
        },
        "required": ["resultList"]
    })


class ResponseHandler(py3_requests.ResponseHandler):
    @staticmethod
    def success(response: Response = None):
        json_addict = ResponseHandler.status_code_200_json_addict(response=response)
        if Draft202012Validator(ValidatorJsonSchema.SUCCESS).is_valid(instance=json_addict):
            return json_addict.get("data", None)
        return None

    @staticmethod
    def result_list(response: Response = None):
        json_addict = ResponseHandler.success(response=response)
        if Draft202012Validator(ValidatorJsonSchema.RESULTLIST).is_valid(instance=json_addict):
            return json_addict.get("resultList", [])
        return []


class Admin(object):
    def __init__(
            self,
            base_url: str = RequestUrl.BASE,
            username: str = "",
            password: str = "",
            cache: Union[diskcache.Cache, redis.Redis, redis.StrictRedis] = None
    ):
        """
        Admin Class
        :param base_url:
        :param username:
        :param password:
        :param cache:
        """
        self.base_url = base_url[:-1] if isinstance(base_url, str) and base_url.endswith("/") else base_url
        self.username = username
        self.password = password
        self.cache = cache
        self.token: dict = Dict()

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
        kwargs.setdefault("method", py3_requests.RequestMethod.POST)
        kwargs.setdefault(
            "response_handler",
            lambda x: isinstance(x, Response) and x.status_code == 200 and x.text.strip() == "null"
        )
        kwargs.setdefault("url", RequestUrl.QUERY_LOGIN_STATE)
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("headers", Dict())
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
        if not self.query_login_state(**Dict(query_login_state_kwargs).to_dict()):
            self.login(**Dict(login_kwargs).to_dict())
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
        kwargs.setdefault("method", py3_requests.RequestMethod.POST)
        kwargs.setdefault("response_handler", ResponseHandler.success)
        kwargs.setdefault("url", RequestUrl.LOGIN)
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("data", Dict())
        kwargs.data.setdefault("username", self.username)
        kwargs.data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        kwargs.data.setdefault("mode", "PASSWORD")
        result = py3_requests.request(**kwargs.to_dict())
        if Draft202012Validator(ValidatorJsonSchema.LOGIN).is_valid(result):
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
        kwargs.setdefault("method", py3_requests.RequestMethod.GET)
        kwargs.setdefault("response_handler", ResponseHandler.success)
        kwargs.setdefault("url", "")
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("headers", Dict())
        kwargs.headers.setdefault("Token", self.token.get("token", ""))
        kwargs.headers.setdefault("Companycode", self.token.get("companyCode", ""))
        return py3_requests.request(**kwargs.to_dict())
