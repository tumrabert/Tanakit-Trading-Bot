
import asyncio
import os
import lighter
from dotenv import load_dotenv
from lighter.signer_client import CreateOrderTxReq
import time
try:
    from .markets import MARKETS
    from .utils import price_to_int, get_client, get_market_price, get_size_multiplier
except ImportError:
    from markets import MARKETS
    from utils import price_to_int, get_client, get_market_price, get_size_multiplier

# Load environment variables from project/.env
load_dotenv()

async def open_limit_order(token, leverage, side, amount_in_usd, price, take_profit_price=None, stop_loss_price=None, reduce_only=False, client=None):
    """
    Opens a limit order with optional TP/SL.
    
    Args:
        token (str): Token symbol (e.g. "BTC", "ETH")
        leverage (int): Leverage multiplier (e.g. 10)
        side (str): "Long" or "Short"
        amount_in_usd (float): Margin Amount in USD (Investment). 
                               (e.g. 100 means 100$ margin. With 10x leverage, position is 1000$)
        price (float): Limit price
        take_profit_price (float, optional): Take profit trigger price
        stop_loss_price (float, optional): Stop loss trigger price
        reduce_only (bool): Whether the order is reduce-only
        client (lighter.SignerClient, optional): Existing client instance
    """
    should_close_client = False
    if client is None:
        client = await get_client()
        should_close_client = True

    # Calculate expiry: 28 days from now in milliseconds
    expiry = int(time.time() * 1000) + 28 * 24 * 60 * 60 * 1000

    try:
        market_index = MARKETS.get(token)
        if market_index is None:
            raise ValueError(f"Unknown token: {token}")

        # Fetch current price for debugging
        try:
            best_bid, best_ask = get_market_price(token)
            print(f"DEBUG: Market {token} (ID {market_index}) - Best Bid: {best_bid}, Best Ask: {best_ask}")
        except Exception as e:
            print(f"DEBUG: Failed to fetch price: {e}")

        # Determine direction
        is_ask = False
        if side.lower() == "short":
            is_ask = True
        elif side.lower() == "long":
            is_ask = False
        else:
            raise ValueError("Side must be 'Long' or 'Short'")

        # Calculate Base Amount
        # User expects amount_in_usd to be the Margin (Investment).
        # So Position Size = Margin * Leverage
        position_size_usd = amount_in_usd * leverage
        coin_amount = position_size_usd / price
        
        # Determine multiplier based on token
        base_amount_multiplier = get_size_multiplier(token)
        base_amount = int(coin_amount * base_amount_multiplier) 
        
        price_int = price_to_int(price, token)
        
        print(f"DEBUG: Placing Order - Token: {token}, Leverage: {leverage}x, Price: {price} ({price_int}), Margin: {amount_in_usd}$, Position: {position_size_usd}$, Units: {base_amount}, Side: {side}")

        # Prepare Main Order
        main_order = CreateOrderTxReq(
            MarketIndex=market_index,
            ClientOrderIndex=0,
            BaseAmount=base_amount,
            Price=price_int,
            IsAsk=1 if is_ask else 0,
            Type=lighter.SignerClient.ORDER_TYPE_LIMIT,
            TimeInForce=lighter.SignerClient.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
            ReduceOnly=1 if reduce_only else 0,
            TriggerPrice=0,
            OrderExpiry=expiry,
        )

        orders_to_place = [main_order]
        grouping_type = None

        # Handle TP/SL
        if take_profit_price or stop_loss_price:
            grouping_type = lighter.SignerClient.GROUPING_TYPE_ONE_TRIGGERS_A_ONE_CANCELS_THE_OTHER
            close_is_ask = not is_ask
            
            # TP Order
            tp_price_int = price_to_int(take_profit_price, token) if take_profit_price else 0
            tp_order = CreateOrderTxReq(
                MarketIndex=market_index,
                ClientOrderIndex=0,
                BaseAmount=0,
                Price=tp_price_int,
                IsAsk=1 if close_is_ask else 0,
                Type=lighter.SignerClient.ORDER_TYPE_TAKE_PROFIT_LIMIT,
                TimeInForce=lighter.SignerClient.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
                ReduceOnly=1,
                TriggerPrice=tp_price_int,
                OrderExpiry=expiry,
            )
            
            # SL Order
            sl_price_int = price_to_int(stop_loss_price, token) if stop_loss_price else 0
            sl_order = CreateOrderTxReq(
                MarketIndex=market_index,
                ClientOrderIndex=0,
                BaseAmount=0,
                Price=sl_price_int,
                IsAsk=1 if close_is_ask else 0,
                Type=lighter.SignerClient.ORDER_TYPE_STOP_LOSS_LIMIT,
                TimeInForce=lighter.SignerClient.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
                ReduceOnly=1,
                TriggerPrice=sl_price_int,
                OrderExpiry=expiry,
            )
            
            orders_to_place.append(tp_order)
            orders_to_place.append(sl_order)
            
        if grouping_type:
             print(f"Placing Grouped Order: {side} {amount_in_usd}$ @ {price}")
             tx = await client.create_grouped_orders(
                grouping_type=grouping_type,
                orders=orders_to_place,
            )
             print(f"Order Placed: {tx}")
             return tx
        else:
            # Simple Limit Order
            print(f"Placing Limit Order: {side} {amount_in_usd}$ @ {price}")
            tx, tx_hash, err = await client.create_order(
                market_index=market_index,
                client_order_index=0,
                base_amount=base_amount,
                price=price_int,
                is_ask=1 if is_ask else 0,
                order_type=lighter.SignerClient.ORDER_TYPE_LIMIT,
                time_in_force=lighter.SignerClient.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
                reduce_only=reduce_only,
                trigger_price=0
            )
            if err:
                raise Exception(f"Error placing order: {err}")
            print(f"Order Placed: {tx_hash}")
            return tx_hash

    finally:
        if should_close_client:
            await client.close()

async def main_test():
    tokens = ["BTC", "ETH", "SOL"]
    leverage = 1
    amount = 10 # 10$ Margin
    
    for token in tokens:
        print(f"\n--- Testing {token} ---")
        try:
            bid, ask = get_market_price(token)
            print(f"Current Price: Bid={bid}, Ask={ask}")
            
            # 1. Long Order (Buy Limit below market)
            # Price: 80% of Bid
            long_price = bid * 0.8
            # TP: 110% of Entry (Above Entry)
            long_tp = long_price * 1.1
            # SL: 90% of Entry (Below Entry)
            long_sl = long_price * 0.9
            
            print(f"Placing LONG {token} at {long_price:.2f} (TP: {long_tp:.2f}, SL: {long_sl:.2f})")
            await open_limit_order(token, leverage, "Long", amount, long_price, 
                                   take_profit_price=long_tp, stop_loss_price=long_sl)
            
            await asyncio.sleep(1) # Small delay
            
            # 2. Short Order (Sell Limit above market)
            # Price: 120% of Ask
            short_price = ask * 1.2
            # TP: 90% of Entry (Below Entry)
            short_tp = short_price * 0.9
            # SL: 110% of Entry (Above Entry)
            short_sl = short_price * 1.1
            
            print(f"Placing SHORT {token} at {short_price:.2f} (TP: {short_tp:.2f}, SL: {short_sl:.2f})")
            await open_limit_order(token, leverage, "Short", amount, short_price, 
                                   take_profit_price=short_tp, stop_loss_price=short_sl)
                                   
            await asyncio.sleep(1) # Small delay

        except Exception as e:
            print(f"Failed to test {token}: {e}")

if __name__ == "__main__":
    asyncio.run(main_test())
    #asyncio.run(open_limit_order("ETH", 10, "Long", 50, 3000, take_profit_price=3200, stop_loss_price=2900))
    #asyncio.run(open_limit_order("BTC", 10, "Long", 50, 90000, take_profit_price=92000, stop_loss_price=89000))
