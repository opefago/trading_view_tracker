from websockets import client
from tenacity import retry, wait_exponential, retry_if_exception_type
import asyncio
import re
from datetime import datetime
from util import strip, unstrip, generate_quote_session, generate_chart_session

trading_symbols = ['BINANCE:LUNAUSDT', 'BITSTAMP:BTCUSD']
websocket_uri = f'wss://data.tradingview.com/socket.io/websocket?from=chart/&date=2022_01_20-13_54'

chart_session = generate_chart_session()
quote_session = generate_quote_session()

# commented out code section for creating charts
# uncomment if you want chart data
init_messages = [
    {"m": "set_data_quality", "p": ["low"]},
    {"m": "set_auth_token", "p": ["unauthorized_user_token"]},
    # {"m": "chart_create_session", "p": [chart_session, ""]},
    # {"m": "resolve_symbol",
    #  "p": [chart_session, "sds_sym_1", "={\"symbol\":\"%s\", \"adjustment\":\"splits\"}" % trading_symbols[0]]},
    # {"m": "create_series", "p": [chart_session, "sds_1", "s1", "sds_sym_1", "D", 300, ""]},
    # {"m": "switch_timezone", "p": [chart_session, "Etc/UTC"]},
    {"m": "quote_create_session", "p": [quote_session]},
]

# adds more than one quote symbol
init_messages \
    .extend([{"m": "quote_add_symbols", "p": [quote_session, trading_symbol, {"flags": ["force_permission"]}]}
             for trading_symbol in trading_symbols])


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
                elif p['m'] == 'qsd':
                    await handle_price_quotes(p['p'][1]['n'], p['p'][1]['v'])
                    pass


async def handle_init_data(data):
    print(f'Init data: {data}')


async def handle_time_scale_data(dates, values):
    print(f'dates: {dates}')
    print(f'vales: {values}')


async def handle_price_change(live_price):
    print(f"Price: {live_price}")


async def handle_price_quotes(trade_symbol, quote):
    print(f"Price Quotes {quote}, for symbol: {trade_symbol}")


@retry(wait=wait_exponential(multiplier=2, min=3, max=100),
       retry=(retry_if_exception_type(ConnectionResetError) | retry_if_exception_type(TimeoutError)))
async def websocket_connect():
    async with client.connect(websocket_uri, extra_headers={
        "Origin": "https://www.tradingview.com"
    }) as websocket:
        await on_receive(websocket)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_connect())
    loop.run_forever()
