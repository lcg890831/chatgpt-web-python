# -*- coding: utf-8 -*-
import os
import json
from typing import Dict, Tuple
import requests
import openai
import hashlib
from flask import *
import xml.etree.ElementTree as ET
import logging
import time



# Define error messages for different status codes
ErrorCodeMessage = {
    401: '[OpenAI] 提供错误的API密钥 | Incorrect API key provided',
    403: '[OpenAI] 服务器拒绝访问，请稍后再试 | Server refused to access, please try again later',
    502: '[OpenAI] 错误的网关 | Bad Gateway',
    503: '[OpenAI] 服务器繁忙，请稍后再试 | Server is busy, please try again later',
    504: '[OpenAI] 网关超时 | Gateway Time-out',
    500: '[OpenAI] 服务器繁忙，请稍后再试 | Internal Server Error',
}

# Set timeout and debug options
timeout_ms = int(os.environ.get("TIMEOUT_MS", 100 * 1000))
disable_debug = os.environ.get("OPENAI_API_DISABLE_DEBUG") == "true"

# Retrieve required environment variables
api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key=api_key
access_token = os.environ.get("OPENAI_ACCESS_TOKEN")
api_base_url = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com")
model = os.environ.get("OPENAI_API_MODEL", "gpt-3.5-turbo")
userMsg = {"role": 'user',"content": ''}
assiMsg = {"role": 'assistant',"content": ''}

# Check if required environment variables are present
if not api_key and not access_token:
    raise ValueError("Missing OPENAI_API_KEY or OPENAI_ACCESS_TOKEN environment variable")

# Set headers for API requests
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

def buildMessage(system_message,message,last_context):
    result =   [
        {"role": "system", "content": system_message}
    ]
    logging.getLogger().info(f'last_context:{last_context}')
    curMessage = {"role": "user", "content": message}
    if last_context.get('parentMessageId','') != '':
        #TODO last message
        preMessage = {}
        #message.append(preMessage)
    result.append(curMessage)
    logging.getLogger().info(f'message:{result}')
    return result
def buildContent(chunk,result):
    result["id"] = chunk['id']
    result["detail"] = chunk
    content = chunk["choices"][0]["delta"].get('content','')
    logging.getLogger().info(f'result:{content}')
    if content!='' :
        result['delta'] = content
        result['text'] = result['text']+result['delta']
    return result



def chat(prompt, options, system_message, temperature, top_p):
    logging.getLogger().info(f'enter:{model}')
    finamsg = buildMessage(system_message,prompt,options)
    apiResp =  openai.ChatCompletion.create(
    model=model,
    top_p=top_p,
    temperature=temperature,
    messages=finamsg,
    stream=True
    )
    return apiResp

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
    
    


