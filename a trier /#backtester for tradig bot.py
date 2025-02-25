#backtester for tradig bot

from binance.client import Client 
import pandas as pd 
import pandas_ta as ta 

#create dataset 

klinesT = Client().get_historical_klines("BTCUSDT",Client.KLINE_INTERVAL_1HOUR, "01 January 2017")
df = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])

#cleaning dataset

del df['ignore'] 
del df['close_time']
del df['quote_av']
del df['trades']
del df['tb_base_av']
del df['tb_quote_av']



df ['close'] = pd.to_numeric(df['close'])
df ['high'] = pd.to_numeric(df['high'])
df ['low'] = pd.to_numeric(df['low'])
df ['open'] = pd.to_numeric(df['open'])


#convert time 

df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')

del df['timestamp']

#indicator defining 

df['SMA200'] = ta.sma(df['close'],length=1)
df['SMA600'] = ta.sma(df['close'],length=2)

#stratégie backtest 
print(df)

t=0
x=0
usdt=1000
btc = 0
lastIndex =  df.first_valid_index()

for index, row in df.iterrows():
    x=x+1
    if df['SMA200'][lastIndex] > df['SMA600'][lastIndex] :
        t=t+1
        btc = usdt / df['close'][index]
        btc = btc - 0.007 * usdt
        usdt = 0 
        print("BUY BTC at",df['close'][index],'$ the', index) 

    if df['SMA200'][lastIndex] < df['SMA600'][lastIndex] :
        t=t+1
        usdt = btc * df['close'][index]
        usdt = usdt - 0.007 * usdt
        btc = 0 
        
        print("SELL BTC at",df['close'][index],'$ the', index)
lastIndex = index 


#test and final result 
finalResult = usdt + btc * df['close'].iloc[-1]
print('Final result',finalResult,"USDT")
print('buy and hold result',(1000 / df['close'].iloc[0]) * df['close'].iloc[-1],'USDT')
print (x)
print (t)