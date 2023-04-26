# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify

import os
import logging
from dotenv import load_dotenv
import json
import openai
import hashlib
from flask import *
import xml.etree.ElementTree as ET
import logging
import time


load_dotenv()
# 配置日志记录器
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为DEBUG
    filename='chatgpt.log',  # 指定日志文件名
    filemode='a',  # 设置写入模式
    format='%(asctime)s - %(levelname)s - %(message)s'  # 设置日志格式
)

app = Flask(__name__)

from chatgpt.openaiApi import chat,buildContent
from middleware.auth import auth
from middleware.limiter_all import limiter_ip_rule
limiter_ip_rule.init_app(app)
@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "authorization, Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

@app.route("/api/config", methods=["POST"])
@auth
def config():
    try:
        response = {}
        return jsonify(response)
    except Exception as error:
        return jsonify({"error": str(error)}), 400

@app.route("/api/chat-process", methods=["POST"])
@auth
def chat_process():
        data = request.json
        prompt = data["prompt"]
        options = data.get("options", {})
        system_message = data["systemMessage"]
        temperature = data["temperature"]
        top_p = data["top_p"]
        apiResp = chat(prompt, options, system_message, temperature, top_p)
        def wrapped_api_response():
            result = {
            "role":"assistant",
            "id":"",
            "parentMessageId":options.get('parentMessageId',''),
            "text":"",
            "delta":"",
            "detail":{}
            }
            
            # Return success response
            first = True
            for chunk in apiResp:
                logging.getLogger().info(f'chunk:{chunk["choices"][0]["delta"]}')
                output = json.dumps(buildContent(chunk,result))
                if(first):
                    first = False
                else:
                    output = '\n'+output
                yield output
        return Response(wrapped_api_response(), content_type='application/octet-stream')


@app.route("/api/session", methods=["POST"])
def session():
    try:
        auth_secret_key = os.environ.get("AUTH_SECRET_KEY")
        has_auth = auth_secret_key!=""
        return jsonify({
            "status": "Success",
            "message": "",
            "data": {"auth": has_auth, "model": 'ChatGPTAPI'},
        })
    except Exception as error:
        return jsonify({
            "status": "Fail",
            "message": str(error),
            "data": None,
        })

@app.route("/api/verify", methods=["POST"])
def verify():
    try:
        data = request.json
        token = data["token"]
        if not token:
            raise ValueError("Secret key is empty")

        auth_secret_key = os.environ.get("AUTH_SECRET_KEY")
        if auth_secret_key != token:
            raise ValueError("密钥无效 | Secret key is invalid")

        return jsonify({
            "status": "Success",
            "message": "Verify successfully",
            "data": None,
        })
    except Exception as error:
        return jsonify({
            "status": "Fail",
            "message": str(error),
            "data": None,
        })

@app.route("/api/wechat", methods=["GET","POST"])
def check_signature():
    app.logger.info(f'wechat enter:{request.data}')
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    echostr = request.args.get('echostr')
    token = 'cheng'
    tmpArr = [token, timestamp, nonce]
    tmpArr.sort()
    tmpStr = ''.join(tmpArr)
    tmpStr = hashlib.sha1(tmpStr.encode('utf-8')).hexdigest()

    if tmpStr == signature:
        root = ET.fromstring(request.data)

        to_user_name = root.find('ToUserName').text
        from_user_name = root.find('FromUserName').text
        content = root.find('Content').text
        logging.getLogger().info(f'content:{content}')
        timestamp = int(time.time())
        #反转发送接收方
        root.find('ToUserName').text = from_user_name
        root.find('FromUserName').text = to_user_name
        root.find('Content').text =  'chatgpt'
        app.logger.info(f'wechat end:{root}')
        return ET.tostring(root, encoding='utf8', method='xml').decode()
    else:
        raise ValueError("Signature check failed")

def wrapApiResp(apiResp,parentMessageId):
    result = {
      "role":"assistant",
      "id":"",
      "parentMessageId":parentMessageId,
      "text":"",
      "delta":"",
      "detail":{}
    }
    
    # Return success response
    first = True
    for chunk in apiResp:
     logging.getLogger().info(f'chunk:{chunk["choices"][0]["delta"]}')
     output = json.dumps(buildContent(chunk,result))
     if(first):
         first = False
     else:
         output = '\n'+output
     return output

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3002)
