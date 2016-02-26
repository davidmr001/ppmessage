# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 PPMessage.
# Guijin Ding, dingguijin@gmail.com
#
#

from .basehandler import BaseHandler

from mdm.api.error import API_ERR
from mdm.db.models import DeviceUser
from mdm.db.models import AppUserData
from mdm.yvredis.genericupdate import generic_update

import json
import copy
import hashlib
import logging

class PPUpdateUserHandler(BaseHandler):
    """
    requst:
    header
    user_uuid
    user_xxx would be update
    user_xxx field must be same with db field of DeviceUser
    
    response:
    error_code

    """
    def _update(self):
        _redis = self.application.redis
        _request = json.loads(self.request.body)

        _app_uuid = _request.get("app_uuid")
        _user_uuid = _request.get("user_uuid")
        _is_distributor_user = _request.get("is_distributor_user")
        
        if _user_uuid == None or _app_uuid == None:
            self.setErrorCode(API_ERR.NO_PARA)
            return

        if _is_distributor_user != None:
            _key = AppUserData.__tablename__ + ".app_uuid." + _app_uuid + ".user_uuid." + _user_uuid + ".is_service_user.True"
            _uuid = _redis.get(_key)
            if _uuid != None:
                _udpated = generic_update(_redis, AppUserData, _uuid, {"is_distributor_user": _is_distributor_user})
                if not _updated:
                    self.setErrorCode(API_ERR.GENERIC_UPDATE)
                    return

        _old_password = _request.get("old_password")
        _user_password = _request.get("user_password")
        if _old_password != None and _user_password != None:
            _key = DeviceUser.__tablename__ + ".uuid." + _user_uuid
            _ex_password = _redis.hget(_key, "user_password")
            _ex_password = hashlib.sha1(_ex_password).hexdigest()
            if _ex_password != _old_password:
                self.setErrorCode(API_ERR.MIS_ERR)
                return

        # remove not table fields
        _data = copy.deepcopy(_request)
        del _data["app_uuid"]
        del _data["user_uuid"]
        if _is_distributor_user != None:
            del _data["is_distributor_user"]
        if _old_password != None:
            del _data["old_password"]
        
        if len(_data) > 0:
            _updated = generic_update(_redis, DeviceUser, _user_uuid, _data)
            if not _updated:
                self.setErrorCode(API_ERR.GENERIC_UPDATE)
                return
        return

    def _Task(self):
        super(PPUpdateUserHandler, self)._Task()
        self._update()
        return
