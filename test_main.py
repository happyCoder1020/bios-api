from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Form, responses, Query, Request, Response, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
#from fastapi.middleware.gzip import GZipMiddleware

from pydantic import BaseModel
import requests
from datetime import datetime, timedelta
import pytz
import base64
import logging

#gradio
#import gradio as gr

import time

import sqlite3
import svn_control

import json
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from gigautils.jarutils import JFrame, JLoader
from gigadb.installer import biosapi_connection,esautomata_connection
from gigadb.esdbsystem import ESQuery
# ^^^ GigaPy Dev

load = JLoader()
load.add_path(r'C:\RoboVeB_SDK')

frame = JFrame(load)
frame.setup(

from updatecode.updatecode import router as updatecode_router
# ^^^ UpdateCodeAPI
from tokenizer.tokenizer import router as tokenizer_router
# ^^^ TokenizerAPI
from biostoken.biostoken import router as biostoken_router
# ^^^ BuildCheck API
from net_doc.api_combine_only_txt import router as net_doc_router
from api_usb_io_sensor.io_sensor import router as io_sensor
# ^^^ Net Doc API
from api_usb_io_sensor.usb import router as usb_api

from superio.api_superio import router as superio_router
from VGA.VGA import router as vga_router

from gitlab_api_app.app import router as gitlab_router


from ssl import create_default_context
import os
import asyncio
import pandas as pd
import io
import re
import pandas as pd
import Pin_count
import httpx
import time
from typing import List

#for logger
from log_streamer import WebSocketLogger, log_message
import sys
import builtins
import functools
import threading

#for logger
log_loop = asyncio.get_event_loop()
logger = WebSocketLogger(sys.stdout, log_loop)
sys.stdout = logger
print = functools.partial(builtins.print, flush=True)

app = FastAPI() #建立一個Fast API application

# HongYi API
app.include_router(updatecode_router)
app.include_router(tokenizer_router)
app.include_router(biostoken_router)
app.include_router(net_doc_router)
app.include_router(superio_router)
app.include_router(io_sensor)
app.include_router(usb_api)
app.include_router(vga_router)
app.include_router(gitlab_router)


oauth2_schema = OAuth2PasswordBearer(tokenUrl="/token") # 执行生成token的地址
server_name = "buildagenttest"
server_port = "8000"

# Configure CORS settings
origins = [
    "http://localhost",
    "http://localhost:" + server_port,
    server_name + ":" + server_port,
    "http://127.0.0.1:8000",
    "http://autoweb"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
TC_server = {
    "fw2tc1": "10.1.9.212",
    "fw2tc2": "10.1.9.213",
    "fw2tc3": "10.1.9.214"
}
#app.add_middleware(GZipMiddleware)

# 伪数据库
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

def fake_hash_password(password: str):
    return "fakehashed" + password


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)  # 从数据库中取出用户信息
    if not user_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password!")
    user = UserInDB(**user_dict)  # 进行用户模型校验
    hashed_password = fake_hash_password(form_data.password)  # 将表单密码进行hash加密
    if not hashed_password == user.hashed_password:  # 表单加密后的密码与数据库中的密码进行比对
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password!")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

build_id = 0
buildList = []
buildques = []
connection = sqlite3.connect('build_agent01.db')
init_cursor = connection.cursor()
#create table
init_cursor.execute('''CREATE TABLE IF NOT EXISTS builds
            (timestamp text, build_type text, build_model text, build_from text, build_rev integer, status integer)''')
connection.close()

connection2 = sqlite3.connect('build_list.db')
init_builds_cursor = connection2.cursor()
#create build table
init_builds_cursor.execute('''CREATE TABLE IF NOT EXISTS sheet_builds
            (build_id integer, timestamp text, build_type text, build_from text, build_branch text, build_model text
            , build_rev integer, build_name text, status integer)''')

connection2.close()

@app.get("/") #指定 API路徑 (get方法)
def read_root():
    return {"Hello": "World"}


@app.get("/console")
async def get_console():

    with open("static/console.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/log/download")
async def download_logs():
    date_str = datetime.now().strftime("%Y%m%d")
    return FileResponse("D:\\server_log\\logs_" + date_str + ".log",
                        media_type='application/octet-stream',
                        filename="logs_" + date_str + ".log")


@app.get("/users/{user_id}")
def read_user(user_id: int, q: Optional[str] = None):
    pass
    return {"user_id": user_id, "q": q}


@app.get("/tasks/{task_id}")
def read_task(task_id: int, q: Optional[str] = None):
    pass
    return {"task_id": task_id, "q": q}


@app.put("/api/build/test/MP/{model}/")
def add_build_mp(model: str, rev: Optional[int] = None, current_user: User = Depends(get_current_active_user)):
    global buildList
#   establish connection
    connection_this = sqlite3.connect('build_agent01.db')
#   create a cursor for connection
    build_cursor = connection_this.cursor()
#   buildList.append({"build_id": this_build_id, "model": model, "rev": rev, "status": "success"})
#   start to insert a data
    build_cursor.execute("INSERT INTO builds VALUES( strftime('%s', 'now'), '" + "test" + "', '" + model + "', '" + "MP" + "', '" + "NULL" + "', " + str(0) + ")")
#   commit the cursor to connection
    connection_this.commit()
#   close the connection
    connection_this.close()
    if (True):
        if buildList is None:
            pass
        return {"model": model, "rev": rev, "status": "success"}
    else:
        return {"status": "fail"}


@app.get("/api/buildqueue/{buildserver}/test/RaptorLake/{model}/")
def add_buildqueue_test(buildserver: str, model: str, rev: Optional[int] = None):
    auth_key = 'amltbXkuY2h1OjE5OTExODk2'
    this_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + auth_key,
    }
    #str(base64.b64encode('auth_key'.encode('UTF-8')))
    build_paras = {
        "buildType": {
            "id": "ReleaseBuild_ReleaseBuild"
        },
        "properties": {
            "property": [
                {
                    "name": "env.A1_Poject",
                    "value": "RaptorLake-GBT"
                },
                {
                    "name": 'env.A7_SVNRepository',
                    "value": 'RaptorLake'
                },
                {
                    "name": "env.A2_Model",
                    "value": model
                },
                {
                    "name": "env.B15_TxBIOS",
                    "value": "TRUE"
                },
                {
                    "name": "env.C1_BuildTool",
                    "value": "46.1"
                },
                {
                    "name": "env.U10_User",
                    "value": "Jimmy.Chu"
                },
            ]
        }
    }
    server_url = "http://" + buildserver + "/app/rest/buildQueue"
    try:
        request_res = requests.post(
                server_url, data=json.dumps(build_paras), headers=this_headers)
        print(request_res.content)

        print(str(request_res.content))
        # test = "1"
        if request_res.status_code == requests.codes.ok:
            reply_text = json.loads(request_res.content)

        elif request_res.content == b'Wrong format of "Authorization" header\r\nTo login manually go to "/login.html" page':
            reply_text = "login failed"

        else:
            reply_text = "check id failed, something wrong"
            print(request_res.content)
    except requests.ReadTimeout:
        # 超時
        print('Timeout')
        reply_text = "Teamcity connection Timeout"
    except requests.ConnectionError:
        # 連線異常
        print('Connection error')
        reply_text = "Teamcity connection error"
    except requests.RequestException:
        # 請求異常
        print('Error')
        reply_text = "send error"

    return reply_text


@app.get("/api/checkqueues/{build_server}/")
async def check_queues(build_server: str):
    error_flag = True
    this_reply = {}
    content_type = ""
    reply_content = ""
    build_servers = {
        "fw2tc1": "10.1.9.212",
        "fw2tc2": "10.1.9.213",
        "fw2tc3": "10.1.9.214"
    }
    auth_key = 'amltbXkuY2h1OjE5OTExODk2'
    this_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + auth_key,
    }
    #this_data = {'locator': 'running:true'}
    this_url = 'https://' + build_servers[build_server] + '/httpAuth/app/rest/buildQueue'
    try:
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(trust_env=False, timeout=timeout, verify=False) as client:
            request_res = await client.get(this_url, headers=this_headers)
        #print(str(request_res.content))
        #test = "1"
        content_type = request_res.headers.get("Content-Type", "").lower()
        reply_content = request_res.text.strip()
        # catch the wrong content
        if "text/html" in content_type:
            error_message = build_server + " has problem"
        # catch the wrong content
        elif reply_content.lower().startswith("<!doctype") or reply_content.lower().startswith("<html"):
            error_message = build_server + " has problem"
        elif request_res.status_code == httpx.codes.OK:
            this_reply = json.loads(request_res.content)
            #reply_text = reply_text0.content['build'][0]['id']
            #reply_text = reply_text0['build']
            error_flag = False
        else:
            error_message = "check server" + build_server + " builds failed, something wrong"
            print (request_res.content)
    except requests.ReadTimeout:
    # 超時
        print('Timeout')
        error_message = "Teamcity connection Timeout"
    except requests.ConnectionError:
    # 連線異常
        print('Connection error')
        error_message = "Teamcity connection error"
    except requests.RequestException:
    # 請求異常
        print('Error')
        error_message = "send error"
    except Exception as e:
    # 其他異常
        print('Error')
        error_message = "Uexpected Error: " + str(e)
    if error_flag == True:
        this_reply = {
            'count': 0,
            'error_message': error_message
        }
        print('[ERROR][check_queues]: ' + this_reply)
        return this_reply
    else:
        print('[INFO][check_queues]: ' + this_reply)
        return this_reply


@app.get("/api/checkbuilds/{build_server}/")
async def check_builds(build_server: str):
    error_flag = True
    this_reply = {}
    build_servers = {
        "fw2tc1": "10.1.9.212",
        "fw2tc2": "10.1.9.213",
        "fw2tc3": "10.1.9.214"
    }
    auth_key = 'amltbXkuY2h1OjE5OTExODk2'
    this_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + auth_key,
    }
    this_data = {'locator': 'running:true'}
    this_url = 'https://' + build_servers[build_server] + '/httpAuth/app/rest/builds'
    try:
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(trust_env=False, timeout=timeout, verify=False) as client:
            request_res = await client.get(this_url, headers=this_headers, params=this_data)
            #request_res = requests.get(this_url, headers=this_headers, params=this_data)
        #print(str(request_res.content))
        #test = "1"
        content_type = request_res.headers.get("Content-Type", "").lower()
        reply_content = request_res.text.strip()
        # catch the wrong content
        if "text/html" in content_type:
            error_message = build_server + " has problem"
        # catch the wrong content
        elif reply_content.lower().startswith("<!doctype") or reply_content.lower().startswith("<html"):
            error_message = build_server + " has problem"
        elif request_res.status_code == httpx.codes.OK:
            this_reply = json.loads(request_res.content)
            #reply_text = reply_text0.content['build'][0]['id']
            #reply_text = reply_text0['build']
            error_flag = False
        else:
            error_message = "check server" + build_server + " builds failed, something wrong"
            print (request_res.content)

    except httpx.ReadTimeout:
    # 超時
        print('Timeout')
        error_message = "Teamcity connection Timeout"
    except httpx.ConnectError:
    # 連線異常
        print('Connection error')
        error_message = "Teamcity connection error"
    except httpx.HTTPError as e:
    # 請求異常
        print('Error')
        error_message = "send error"
    except Exception as e:
    # 其他異常
        print('Error')
        error_message = "Uexpected Error: " + str(e)
    #add server info
    this_reply['server'] = build_server
    if error_flag == True:
        this_reply = {
            'server': build_server,
            'count': 0,
            'error_message': error_message
        }
        print('[ERROR][check_builds]: ' + this_reply)
        return this_reply
    else:
        print('[INFO][check_builds]: ' + this_reply)
        return this_reply

