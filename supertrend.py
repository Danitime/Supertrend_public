import ccxt
import config
import schedule
import time
import send_mail
import traceback
import get_coins

import pandas as pd



pd.set_option('display.max_rows', None)

import warnings
warnings.filterwarnings('ignore')

from datetime import datetime

currency = config.CURRENCY

exchange = ccxt.binance({
    "apiKey": config.API_KEY,
    "secret": config.API_SECRET
})



def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df


def check_buy_sell_signals(df, coin):
    #print(f"Checking for buy and sell signals for {coin}")
    #print(df.tail(5))

    if len(df.index) > 7:
        last_row_index = len(df.index) - 1
        previous_row_index = last_row_index - 1
        close = df["close"].tail(1).item()

        if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
            print(f"+++++ Changed to uptrend, checking buy signal for {coin} +++++")
            send_mail.append_msg(f"{coin} hat zu einer Aufwaertsbewegung gewechselt.")
            in_position = check_position(close, coin)
            enough_money = check_balance()
            if in_position == 0 and enough_money:
                amount = 100 / close
                order = exchange.create_market_buy_order(f'{coin}/{currency}', amount)
                print(order)
                send_mail.append_msg(f"{coin} wurde gekauft. Orderinformationen: {order}")
            else:
                if in_position == 0:
                    print("Did not buy: Not enough money")
                    send_mail.append_msg(f"{coin} wurde nicht gekauft. Grund: Wir besitzen nicht genug Geld!")
                else:
                    print("Did not buy: You are already in position")
                    send_mail.append_msg(f"{coin} wurde nicht gekauft. Grund: Wir besitzen bereits welche!")
        
        if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
            print(f"----- Changed to downtrend, checking sell signal for {coin} -----")
            send_mail.append_msg(f"{coin} hat zu einer Abwaertsbewegung gewechselt.")
            in_position = check_position(close, coin)
            if in_position > 0:
                order = exchange.create_market_sell_order(f'{coin}/{currency}', in_position)
                print(order)
                send_mail.append_msg(f"{coin} wurde verkauft. Orderinformationen: {order}")
            else:
                print("Did not sell: You are not in position")
                send_mail.append_msg(f"{coin} wurde nicht verkauft. Wir besitzen naemlich keine!")

def check_position(close, coin):
    #print("Checking position for: ", coin)
    balances = exchange.fetch_free_balance()
    
    for balance in balances:
        if balance == coin:
            if balances[balance] > (5 / close): #check if there are more than 5 currency worth of pair in portfolio
                #print("Position found. Returning position: ", balances[balance])
                return balances[balance]
            else:
                return 0
    
    return 0

def check_balance():
    balances = exchange.fetch_free_balance()
    print(balances[f"{currency}"])
    if balances[f"{currency}"] > 110:
        return True
    else:
        return False



def run_bot():
    try:
        coins = get_coins.get_tradeable_coins(exchange, currency)
        send_mail.append_msg(f"Die aktuellen handelbaren Paare fuer {currency} sind: \n{coins}")
        print(f"Fetching bars for {datetime.now().isoformat()}")
        
        for coin in coins:
            #print(coin)
            bars = exchange.fetch_ohlcv(f'{coin}/{currency}', timeframe='1d', limit=100)
            df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            supertrend_data = supertrend(df)
            
            check_buy_sell_signals(supertrend_data, coin)
        
        send_mail.send("Daily Nachricht von deinem Bot.")

    except Exception:
        send_mail.append_msg("\n\n\n")
        send_mail.append_msg(traceback.format_exc())
        send_mail.send("Ein Error ist aufgetreten")



#schedule.every(10).seconds.do(run_bot)
schedule.every().day.at("02:01").do(run_bot)
#schedule.every(1).hours.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)