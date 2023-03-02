from binance.client import Client 
import pandas as pd 
import pandas_ta as ta 

#create dataset 

klinesT = Client().get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "01 January 2017")
df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

# cleaning dataset

del df['ignore']
del df['close_time']
del df['quote_av']
del df['trades']
del df['tb_base_av']
del df['tb_quote_av']

df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

#convert time 
df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')
del df['timestamp']

#indicator defining 
df['SMA20'] = ta.sma(df['close'], length=200)
df['SMA60'] = ta.sma(df['close'], length=600)

#stratégie backtest 
print(df)
usdt = 1000
btc = 0
lastIndex = df.first_valid_index()
buy_price = None

for index, row in df.iterrows():
    if df['SMA20'][lastIndex] > df['SMA60'][lastIndex]:
        if btc == 0:
            btc = usdt / df['close'][index]
            usdt = 0
            buy_price = df['close'][index]
            print("BUY BTC at", buy_price, '$ the', index) 
    elif df['SMA20'][lastIndex] < df['SMA60'][lastIndex]:
        if btc > 0:
            usdt = btc * df['close'][index]
            btc = 0
            sell_price = df['close'][index]
            print("SELL BTC at", sell_price, '$ the', index)
            print("Profit:", sell_price / buy_price)
    lastIndex = index

#test and final result 
finalResult = usdt + btc * df['close'].iloc[-1]
print('Final result',finalResult,"USDT")
print('buy and hold result', (1000 / df['close'].iloc[0]) * df['close'].iloc[-1], 'USDT')
