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

request_urls = Dict()
request_urls.base = "https://sq.wisharetec.com/"
request_urls.login = "/manage/login"
request_urls.query_login_state = "/old/serverUserAction!checkSession.action"
request_urls.query_community_with_paginator = "/manage/communityInfo/getAdminCommunityList"
request_urls.query_community_detail = "/manage/communityInfo/getCommunityInfo"
request_urls.query_room_with_paginator = "/manage/communityRoom/listCommunityRoom"
request_urls.query_room_detail = "/manage/communityRoom/getFullRoomInfo"
request_urls.query_room_export = "/manage/communityRoom/exportDelayCommunityRoomList"
request_urls.query_register_user_with_paginator = "/manage/user/register/list"
request_urls.query_register_user_detail = "/manage/user/register/detail"
request_urls.query_register_user_export = "/manage/user/register/list/export"
request_urls.query_register_owner_with_paginator = "/manage/user/information/register/list"
request_urls.query_register_owner_detail = "/manage/user/information/register/detail"
request_urls.query_register_owner_export = "/manage/user/information/register/list/export"
request_urls.query_unregister_owner_with_paginator = "/manage/user/information/unregister/list"
request_urls.query_unregister_owner_detail = "/manage/user/information/unregister/detail"
request_urls.query_unregister_owner_export = "/manage/user/information/unregister/list/export"
request_urls.query_shop_goods_category_with_paginator = "/manage/productCategory/getProductCategoryList"
request_urls.query_shop_goods_with_paginator = "/manage/shopGoods/getAdminShopGoods"
request_urls.query_shop_goods_detail = "/manage/shopGoods/getShopGoodsDetail"
request_urls.save_shop_goods = "/manage/shopGoods/saveSysShopGoods"
request_urls.update_shop_goods = "/manage/shopGoods/updateShopGoods"
request_urls.query_shop_goods_push_to_store = "/manage/shopGoods/getGoodsStoreEdits"
request_urls.save_shop_goods_push_to_store = "/manage/shopGoods/saveGoodsStoreEdits"
request_urls.query_store_product_with_paginator = "/manage/storeProduct/getAdminStoreProductList"
request_urls.query_store_product_detail = "/manage/storeProduct/getStoreProductInfo"
request_urls.update_store_product = "/manage/storeProduct/updateStoreProductInfo"
request_urls.update_store_product_status = "/manage/storeProduct/updateProductStatus"
request_urls.query_business_order_with_paginator = "/manage/businessOrderShu/list"
request_urls.query_business_order_detail = "/manage/businessordershu/view"
request_urls.query_business_order_export_1 = "/manage/businessOrder/exportToExcelByOrder"
request_urls.query_business_order_export_2 = "/manage/businessOrder/exportToExcelByProduct"
request_urls.query_business_order_export_3 = "/manage/businessOrder/exportToExcelByOrderAndProduct"
request_urls.query_work_order_with_paginator = "/old/orderAction!viewList.action"
request_urls.query_work_order_detail = "/old/orderAction!view.action"
request_urls.query_work_order_export = "/manage/order/work/export"
request_urls.query_parking_auth_with_paginator = "/manage/carParkApplication/carParkCard/list"
request_urls.query_parking_auth_detail = "/manage/carParkApplication/carParkCard"
request_urls.update_parking_auth = "/manage/carParkApplication/carParkCard"
request_urls.query_parking_auth_audit_with_paginator = "/manage/carParkApplication/carParkCard/parkingCardManagerByAudit"
request_urls.query_parking_auth_audit_check_with_paginator = "/manage/carParkApplication/getParkingCheckList"
request_urls.update_parking_auth_audit_status = "/manage/carParkApplication/completeTask"
request_urls.query_export_with_paginator = "/manage/export/log"
request_urls.upload = "/upload"

validator_json_schemas = Dict()
validator_json_schemas.normal = Dict({
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
validator_json_schemas.login = Dict({
    "type": "object",
    "properties": {
        "token": {"type": "string", "minLength": 1},
        "companyCode": {"type": "string", "minLength": 1},
    },
    "required": ["token", "companyCode"],
})
validator_json_schemas.result_list = Dict({
    'type': 'object',
    'properties': {
        "resultList": {"type": "array"},
    },
    "required": ["resultList"]
})


def normal_response_handler(response: Response = None):
    if isinstance(response, Response) and response.status_code == 200:
        json_addict = Dict(response.json())
        if Draft202012Validator(validator_json_schemas.normal).is_valid(instance=json_addict):
            return json_addict.get("data", Dict())
        return Dict()
    raise Exception(f"Response Handler Error {response.status_code}|{response.text}")


def result_list_response_handler(response: Response = None):
    result = normal_response_handler(response=response)
    if Draft202012Validator(validator_json_schemas.resultList).is_valid(instance=result):
        return result.get("resultList", [])
    return []


class Admin(object):
    def __init__(
            self,
            base_url: str = request_urls.base,
            username: str = "",
            password: str = "",
            cache: Union[diskcache.Cache, redis.Redis, redis.StrictRedis] = None
    ):
        self.base_url = base_url[:-1] if isinstance(base_url, str) and base_url.endswith("/") else base_url
        self.username = username
        self.password = password
        self.cache = cache
        self.token: dict = Dict({})

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
        kwargs.setdefault("url", f"{request_urls.query_login_state}")
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
        kwargs.setdefault("response_handler", normal_response_handler)
        kwargs.setdefault("url", request_urls.login)
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("data", Dict())
        kwargs.data.setdefault("username", self.username)
        kwargs.data.setdefault("password", hashlib.md5(self.password.encode("utf-8")).hexdigest())
        kwargs.data.setdefault("mode", "PASSWORD")
        result = py3_requests.request(**kwargs.to_dict())
        if Draft202012Validator(validator_json_schemas.login).is_valid(result):
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
        kwargs.setdefault("response_handler", normal_response_handler)
        kwargs.setdefault("url", f"")
        if not kwargs.get("url", "").startswith("http"):
            kwargs["url"] = self.base_url + kwargs["url"]
        kwargs.setdefault("headers", Dict({}))
        kwargs.headers.setdefault("Token", self.token.get("token", ""))
        kwargs.headers.setdefault("Companycode", self.token.get("companyCode", ""))
        return py3_requests.request(**kwargs.to_dict())
