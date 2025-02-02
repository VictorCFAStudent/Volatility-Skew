import numpy as np
import pandas as pd
import yfinance as yf
from matplotlib import pyplot as plt
from datetime import datetime
from scipy import stats as ss

#This is a Skew Volatility Modeling program

#Creating Stock class in order to get stock and stock's options data
class StockData :

    #Gathering stock data ()
    def __init__(self, stock):
        self.ticker = yf.Ticker(stock) #ticker
        self.expirations = self.ticker.options #maturities available
        self.yesterday_stock_data = self.ticker.history(period = '1d') 
        self.current_price = self.yesterday_stock_data['Close'].iloc[-1] #getting current stock price

    #Gathering options data
    def gather_options_data(self, options_type):
        options_dict  = {} 
        for expiry in self.expirations : 
            options_data = self.ticker.option_chain(expiry)

            if options_type == 'calls' :
                calls = options_data.calls
                options_dict[expiry]= calls
            elif options_type == 'puts' :
                puts = options_data.puts
                options_dict[expiry]= puts

        return options_dict

    #Cleaning options data
    def clean_options_data(self, options_dict):
        min_volatility = 0.001
        max_spread = 0.1
        columns_to_remove = ['contractSymbol', 'openInterest', 'contractSize', 'currency']
        cleaned_options = {}
        for expiry in options_dict.keys():
            df = options_dict[expiry].drop(columns=columns_to_remove)
            df = df.dropna(subset=['impliedVolatility'])
            df = df[df['impliedVolatility'] > min_volatility]
            df['spreadBidAsk'] = (df['ask'] - df['bid']) / df['ask']
            df = df[df['spreadBidAsk'] <= max_spread]
            if not df.empty:
                cleaned_options[expiry] = df
        return cleaned_options

#This class allows us to facilitate the reading of the code, especially when it comes to model   
class SkewModelizer:

    def __init__(self, cleaned_options, options_type, maturity, current_price, ticker, max_strike_ratio):
        self.ticker = ticker
        self.options_type = options_type
        self.maturity = maturity
        self.current_price = current_price 
        self.strike_price_ratio = cleaned_options[maturity]['strike'] / self.current_price 
        self.removing_outliers = cleaned_options[maturity][self.strike_price_ratio <= max_strike_ratio]
        self.xaxis = self.removing_outliers['strike'] / self.current_price
        self.yaxis = self.removing_outliers['impliedVolatility']

    def model(self):
        plt.plot(self.xaxis, self.yaxis, marker='o', label=f'{self.options_type}')
        plt.xlabel('K/S ratio', fontsize=12, weight='bold')
        plt.ylabel('Implied Volatility', fontsize=12, weight='bold')
        plt.legend(fontsize = 12)

#Getting required inputs from user, as the ticker and the option type used as basis of analysis
ticker = input("Input the ticker to analyze ").capitalize() 
stock = StockData(ticker)
options_type = input("From which kind of options you want to model the Skew ? (calls / puts / both) ")  
while options_type not in ["calls","puts","both"]:
        print("Invalid option type. Please choose one from calls / puts / both.")
        options_type = input("Which kind of options: ")  
        
#if we decide to use calls and puts
if options_type == 'both' :

    #Getting call dictionnary
    calls_data_dict = stock.gather_options_data('calls')
    clean_calls_data_dict = stock.clean_options_data(calls_data_dict)
    #Getting put dictionnary
    puts_data_dict = stock.gather_options_data('puts')
    clean_puts_data_dict = stock.clean_options_data(puts_data_dict)

    #Getting common maturities to suggest comparable options only 
    common_maturities = [maturity for maturity in clean_calls_data_dict if maturity in clean_puts_data_dict]
    if not common_maturities :
        print("No maturities avalaible after cleaning the data base.")
        exit()

    #User input desired maturity
    print('Available maturities: ', common_maturities)
    maturity = input("Input one of the maturity above ")
    while maturity not in common_maturities:
        print("Invalid maturity. Please choose one from the list.")
        maturity = input("Input one of the maturity above: ")   

    #Initializing attributs to dictionnaries we want to model
    modelling_calls = SkewModelizer(clean_calls_data_dict, 'calls', maturity, stock.current_price, ticker, max_strike_ratio = 2)
    modelling_puts = SkewModelizer(clean_puts_data_dict, 'puts', maturity, stock.current_price, ticker, max_strike_ratio=2)

    #Modelization
    plt.figure(figsize = (14, 8))
    modelling_calls.model()
    modelling_puts.model()
    plt.title(f'{ticker} Volatility Skew Modeling, maturity = {maturity}', fontsize=16)
    plt.show()

else :
    #If we decide not to use only calls or only puts options
    options_dict = stock.gather_options_data(options_type)
    clean_options_data_dict = stock.clean_options_data(options_dict)

    #Displaying available maturities and getting the desired one
    maturities = list(clean_options_data_dict.keys())
    print('Available maturities: ', maturities)
    maturity = input("Input one of the maturity above ")
    while maturity not in maturities:
        print("Invalid maturity. Please choose one from the list.")
        maturity = input("Input one of the maturity above: ")   

    #Initializing attributs to the dictionnary we want to model
    modeling_dict = SkewModelizer(clean_options_data_dict, options_type, maturity, stock.current_price, ticker, max_strike_ratio=2)
    
    #Modelization
    plt.figure(figsize=(12, 8))
    final_dict = modeling_dict.model()
    plt.title(f'{ticker} Volatility Skew Modeling from {options_type[:-1]} options, maturity = {maturity}', fontsize=16)
    plt.show()
