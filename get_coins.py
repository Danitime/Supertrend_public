import pandas as pd




def get_tradeable_coins(exchange, currency):
    #print("Getting tradeable coins")
    tradeable_pairs = exchange.load_markets()
    coins = []
    for tradeable_pair in tradeable_pairs:
        if f"/{currency}" in tradeable_pair:
            tradeable_coin = tradeable_pair.replace(f"/{currency}", "")
            coins.append(tradeable_coin)

    #log current coins
    coins_df = pd.DataFrame(coins)
    coins_df.to_csv("tradeable_coins.csv")

    #print(f"Tradeable coins for {currency} detected: ", coins)
    #send_mail.append_msg("Tradeable coins detected:")
    #send_mail.append_msg(str(coins))
    return coins