from datetime import datetime

from logzero import logger, logfile
from fastapi import FastAPI, Body
from fastapi import FastAPI, Request, HTTPException 
from fastapi.responses import JSONResponse 
import json
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import uvicorn
import json
cwd = os.path.dirname(os.path.abspath(__file__))

timestamp = datetime.now().strftime("%Y-%m-%d")
logfile(os.path.join(cwd, f"webhook_load_balancer_{timestamp}.log"))


## config parser setup
import configparser
config = configparser.ConfigParser()
config.read(os.path.join(cwd,"config.ini"))
port_number = int(config["NGROK_CONFIG"]["port_number"])
auth_token = config["NGROK_CONFIG"]["auth_token"]
domain = config["NGROK_CONFIG"]["domain"]
target_domain = config["NGROK_CONFIG"]["target_domain"]


## FastAPI setup
app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## 8001 routes
@app.post("/webhook")
async def post_webhook_processor(data: list[dict] = Body()):
    # async with httpx.AsyncClient() as client:
    #     api_url = f"http://{target_domain}:8001/webhook"
    #     return await client.post(api_url, json=data)
    logger.info(f"webhook-{data=}")
    api_url = f"http://{target_domain}:8001/webhook"
    logger.info(requests.post(api_url, json=data).content)
    return {}



## 8002 routes
@app.post("/webhook2")
async def post_webhook2_processor(data: list[dict] = Body()):
    # async with httpx.AsyncClient() as client:
    logger.info(f"webhook2-{data=}")
    api_url = f"http://{target_domain}:8002/webhook2"
    logger.info(requests.post(api_url, json=data))
    return {}
    # return await client.post(api_url, json=data)


## 8004 routes
@app.post("/webhook_greek")
async def post_webhook3_processor(data: list[dict] = Body()):
    # async with httpx.AsyncClient() as client:
    logger.info(f"webhook_greek-{data=}")
    api_url = f"http://192.168.173.185:8004/webhook_greek"
    logger.info(requests.post(api_url, json=data))
    return {}
    # return await client.post(api_url, json=data)

@app.post("/webhook3_bkp")
async def post_webhook4_processor(data: list[dict] = Body()):
    # async with httpx.AsyncClient() as client:
    logger.info(f"webhook3_bkp-{data=}")
    api_url = f"http://{target_domain}:8777/webhook3"
    logger.info(requests.post(api_url, json=data))
    return {}
    # return await client.post(api_url, json=data)


@app.post("/webhook3") 
async def accept_data(request: Request): 
    try: 
        data = await request.json() 
        logger.info(f"webhook3-{data=}")
        api_url = f"http://{target_domain}:8777/webhook3"
        logger.info(requests.post(api_url, json=data))
        return {}
    except json.JSONDecodeError: 
        data = await request.body() 
        data_str = data.decode("utf-8") 
        logger.info(f"webhook3-{data_str=}")
        api_url = f"http://{target_domain}:8777/webhook3"
        logger.info(requests.post(api_url, data=data_str))
        return {}
@app.post("/webhook4") 
async def accept_data(request: Request): 
    try: 
        data = await request.json()
        logger.info(f"webhook4-{data=}") 
        api_url = f"http://{target_domain}:8778/webhook4"
        logger.info(requests.post(api_url, json=data))
        return {}
    except json.JSONDecodeError: 
        data = await request.body() 
        data_str = data.decode("utf-8") 
        logger.info(f"webhook4-{data_str=}")
        api_url = f"http://{target_domain}:8778/webhook4"
        logger.info(requests.post(api_url, data=data_str))
        return {}

@app.post("/webhook_multileg")
async def webhook_multileg_processor(request: Request):
    data = await request.json() 
    logger.info(f"webhook_multileg-{data=}")
    api_url = f"http://{target_domain}:8051/webhook_multileg"
    logger.info(requests.post(api_url, json=data))
    return {}

@app.post("/webhook_multileg1")
async def webhook_multileg_processor(request: Request):
    data = await request.json()
    logger.info(f"webhook_multileg1-{data=}") 
    api_url = f"http://{target_domain}:8050/webhook_multileg"
    logger.info(requests.post(api_url, json=data))
    return {}


@app.post("/webhook_one_side")
async def webhook_multileg_processor(request: Request):
    data = await request.json()
    logger.info(f"webhook_one_side-{data=}") 
    api_url = f"http://{target_domain}:8900/webhook_one_side"
    logger.info(requests.post(api_url, json=data))
    return {}


@app.post("/webhook_both_side")
async def webhook_multileg_processor(request: Request):
    data = await request.json()
    logger.info(f"webhook_both_side-{data=}") 
    api_url = f"http://{target_domain}:8902/webhook_both_side"
    logger.info(requests.post(api_url, json=data))
    return {}




## Boilerplate code
def configure():
    global ngrok, public_url
    from pyngrok import ngrok, conf
    pyngrok_config = conf.PyngrokConfig(auth_token=auth_token)
    conf.set_default(pyngrok_config)
    public_url = ngrok.connect(domain=domain, addr=port_number).public_url
    logger.info(f'ngrok public url is: {public_url}')
    print(f'ngrok public url is: {public_url}')

if __name__ == "__main__":
    configure()
    uvicorn.run(app, host="127.0.0.1", port=port_number)