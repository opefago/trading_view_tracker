from websockets import client
import asyncio
import re
from datetime import datetime
from util import strip, unstrip, get_random_alpha
ticker = 'BINANCE:LUNAUSDT'
websocket_uri = f'wss://data.tradingview.com/socket.io/websocket?from=chart/&date=2022_01_20-13_54'
chart_session = f"cs_{get_random_alpha(10)}"
quote_session = f"qs_{get_random_alpha(10)}"

init_messages = [
    {"m": "set_data_quality", "p": ["low"]},
    {"m": "set_auth_token", "p": ["unauthorized_user_token"]},
    {"m": "chart_create_session", "p": [chart_session, ""]},
    {"m": "resolve_symbol",
     "p": [chart_session, "sds_sym_1", "={\"symbol\":\"%s\", \"adjustment\":\"splits\"}" % ticker]},
    {"m": "create_series", "p": [chart_session, "sds_1", "s1", "sds_sym_1", "D", 300, ""]},
    {"m": "switch_timezone", "p": [chart_session, "Etc/UTC"]},
]


async def init_tradeview_socket(websocket):
    for m in init_messages:
        await websocket.send(unstrip(m))


def is_keep_alive(text):
    no_data_reg = re.match('~m~\\d+~m~~h~\\d+', text)
    if not no_data_reg:
        return False
    return True


async def on_receive(websocket):
    data = await websocket.recv()
    await handle_init_data(strip(data))
    await init_tradeview_socket(websocket)
    while True:
        data = await websocket.recv()
        if is_keep_alive(data):
            await websocket.send(data)
        else:
            payloads = strip(data)
            for p in payloads:
                if p["m"] == "timescale_update":
                    dates = [
                        datetime.fromtimestamp(t["v"][0])
                        for t in p["p"][1]["sds_1"]["s"]
                    ]
                    values = [
                        t["v"][4]
                        for t in p["p"][1]["sds_1"]["s"]
                    ]
                    await handle_time_scale_data(dates, values)
                elif p['m'] == 'du':
                    await handle_price_change(p['p'][1]['sds_1']['s'])


async def handle_init_data(data):
    print(f'Init data: {data}')


async def handle_time_scale_data(dates, values):
    print(f'dates: {dates}')
    print(f'vales: {values}')


async def handle_price_change(live_price):
    print(f"Price: {live_price}")


async def websocket_connect():
    async with client.connect(websocket_uri, extra_headers={
        "Origin": "https://www.tradingview.com"
    }) as websocket:
        await on_receive(websocket)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_connect())
    loop.run_forever()
