# Import necessary libraries
import pandas as pd
from binance.client import Client
import ta
import pandas_ta as pda
import matplotlib.pyplot as plt

# Define Binance Client
client = Client()

# Define the cryptocurrency pair, start date, and time interval
pairName = "BTCUSDT"
startDate = "01 Jan 2017"
timeInterval = Client.KLINE_INTERVAL_12HOUR

# Load historical price data from Binance API
klinesT = client.get_historical_klines(pairName, timeInterval, startDate)

# Create a DataFrame from the data
df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

# Convert relevant columns to numeric types
df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

# Set the 'timestamp' column as the index and convert it to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Drop unnecessary columns
df.drop(columns=['close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'], inplace=True)

# Calculate technical indicators
df['EMA90'] = ta.trend.ema_indicator(close=df['close'], window=90)
df['STOCH_RSI'] = ta.momentum.stochrsi(close=df['close'], window=14, smooth1=3, smooth2=3)

# Define the Supertrend parameters
ST_length = 20
ST_multiplier1 = 2.0
ST_multiplier2 = 4.0
ST_multiplier3 = 8.0

supertrend1 = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier1)['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier1)]
supertrend2 = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier2)['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier2)]
supertrend3 = pda.supertrend(df['high'], df['low'], df['close'], length=ST_length, multiplier=ST_multiplier3)['SUPERT_'+str(ST_length)+"_"+str(ST_multiplier3)]

# Calculate the derivative of SuperTrend
df['SUPER_TREND_DERIVATIVE1'] = supertrend1.diff()
df['SUPER_TREND_DERIVATIVE2'] = supertrend2.diff()
df['SUPER_TREND_DERIVATIVE3'] = supertrend3.diff()

# Print a message indicating that the data has been loaded
print("Data loaded successfully")


dfTest = df.copy()


# dfTest = df['2021-01-01':]
dt = None
dt = pd.DataFrame(columns = ['date','position', 'price', 'frais' ,'fiat', 'coins', 'wallet', 'drawBack'])

# -- You can change variables below --
leverage = 3
wallet = 1000
makerFee = 0.0002
takerFee = 0.0007

# -- Do not touch these values --
initalWallet = wallet
lastAth = wallet
previousRow = dfTest.iloc[0]
stopLoss = 0
takeProfit = 500000
orderInProgress = ''
longIniPrice = 0
shortIniPrice = 0
longLiquidationPrice = 500000
shortLiquidationPrice = 0
wallet_values = [1000]
test = 1

# -- Condition to open Market LONG --
def openLongCondition(row, previousRow):
  if row['SUPER_TREND_DERIVATIVE1'] + row['SUPER_TREND_DERIVATIVE2'] + row['SUPER_TREND_DERIVATIVE3'] > 0 + row['STOCH_RSI'] > 0.8 :
   return True 
  else:
   return False 

# -- Condition to close Market LONG --
def closeLongCondition(row, previousRow):
  if row['SUPER_TREND_DERIVATIVE1'] + row['SUPER_TREND_DERIVATIVE2'] + row['SUPER_TREND_DERIVATIVE3'] <= 0 :
   return True
  else:
   return False

# -- Iteration on all your price dataset (df) --
for index, row in dfTest.iterrows():

    # -- If there is an order in progress --
    if orderInProgress != '':
        # -- Check if there is a LONG order in progress --
        if orderInProgress == 'LONG':
            # -- Check Liquidation --
            if row['low'] < longLiquidationPrice:
                print('/!\ YOUR LONG HAVE BEEN LIQUIDATED the',index)
                break
            
                # -- Check If you have to close the LONG --
            if closeLongCondition(row, previousRow) == True:
                orderInProgress = ''
                closePrice = row['close']
                closePriceWithFee = row['close'] - takerFee * row['close']
                pr_change = (closePriceWithFee - longIniPrice) / longIniPrice
                wallet = wallet + wallet*pr_change*leverage
                
                if wallet > lastAth:
                    lastAth = wallet
                myrow ={'date': index, 'position': "LONG", 'reason': 'Close Long Market', 'price': closePrice,
                        'frais': takerFee * wallet * leverage, 'wallet': wallet, 'drawBack': (wallet-lastAth)/lastAth}
                dt = pd.concat([dt, pd.DataFrame.from_records([myrow])], ignore_index=True)
            else :
                wallet_values.append(wallet) 
    
    
    if orderInProgress == '':
        # -- Check If you have to open a LONG --
        if openLongCondition(row, previousRow) == True:
            orderInProgress = 'LONG'
            closePrice = row['close']
            longIniPrice = row['close'] + takerFee * row['close']
            tokenAmount = (wallet * leverage) / row['close']
            longLiquidationPrice = longIniPrice - (wallet/tokenAmount)

            # -- You can uncomment the line below if you want to see logs --
            # print('Open LONG at', closePrice, '$ the', index, '| Liquidation price :', longLiquidationPrice)

            # -- Add the trade to DT to analyse it later --
            myrow ={'date': index, 'position': "Open Long", 'reason': 'Open Long Market', 'price': closePrice,
                     'frais': takerFee * wallet * leverage, 'wallet': wallet, 'drawBack': (wallet-lastAth)/lastAth}
            dt = pd.concat([dt, pd.DataFrame.from_records([myrow])], ignore_index=True)
        wallet_values.append(wallet) 

# -- BackTest Analyses --
dt = dt.set_index(dt['date'])
dt.index = pd.to_datetime(dt.index)
dt['resultat%'] = dt['wallet'].pct_change()*100

dt['tradeIs'] = ''
dt.loc[dt['resultat%'] > 0, 'tradeIs'] = 'Good'
dt.loc[dt['resultat%'] < 0, 'tradeIs'] = 'Bad'

iniClose = dfTest.iloc[0]['close']
lastClose = dfTest.iloc[len(dfTest)-1]['close']
holdPercentage = ((lastClose - iniClose)/iniClose)
holdWallet = holdPercentage * leverage * initalWallet
algoPercentage = ((wallet - initalWallet)/initalWallet)
vsHoldPercentage = ((wallet - holdWallet)/holdWallet) * 100
# -- BackTest Analyses --
dt = dt.set_index(dt['date'])
dt.index = pd.to_datetime(dt.index)
dt['resultat%'] = dt['wallet'].pct_change()*100

dt['tradeIs'] = ''
dt.loc[dt['resultat%'] > 0, 'tradeIs'] = 'Good'
dt.loc[dt['resultat%'] < 0, 'tradeIs'] = 'Bad'

iniClose = dfTest.iloc[0]['close']
lastClose = dfTest.iloc[len(dfTest)-1]['close']
holdPercentage = ((lastClose - iniClose)/iniClose)
holdWallet = holdPercentage * leverage * initalWallet
algoPercentage = ((wallet - initalWallet)/initalWallet)
vsHoldPercentage = ((wallet - holdWallet)/holdWallet) * 100

print (dfTest)

print (wallet)
#set value for the plot 
dfTest.index = pd.to_datetime(dfTest.index)
wallet_values = wallet_values[:-1]

# ploting 
plt.plot(dfTest.index, wallet_values)
plt.title("Wallet Value over time")
plt.xlabel("index")
plt.ylabel("Wallet Value")
plt.show()
