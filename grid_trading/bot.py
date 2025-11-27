"""
Lighter Grid Trading Bot (Core Logic)
"""
import asyncio
import signal
import logging
import time
from datetime import datetime
import lighter
import sys
from pathlib import Path

# Add project root to sys.path to allow importing lighter_tool
sys.path.append(str(Path(__file__).resolve().parent.parent))

from lighter_tool.utils import price_to_int, get_size_multiplier, get_client, PRICE_PRECISIONS
from lighter_tool.markets import MARKETS
from lighter_tool.orders import place_limit_order, cancel_order

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class GridTradingBot:
    def __init__(self, token="BTC", direction="NEUTRAL", leverage=10, grid_count=20, investment=100, lower_price=90000, upper_price=110000):
        # Strategy config
        self.token = token
        self.direction = direction
        self.leverage = int(leverage)
        self.grid_count = int(grid_count)
        self.investment = float(investment)
        self.lower_price = float(lower_price)
        self.upper_price = float(upper_price)
        
        self.market_index = MARKETS.get(token)
        if self.market_index is None:
            raise ValueError(f"Unknown token: {token}")
        
        self.client = None
        self.api_client = None
        self.order_api = None
        self.account_api = None
        
        self.order_index = 0
        # Create reverse mapping for ID -> Symbol
        self.id_to_symbol = {v: k for k, v in MARKETS.items()}
        self.market_symbol = self.id_to_symbol.get(self.market_index, f"Market{self.market_index}")

        # Auto-refill tracking
        self.running = True
        self.grid_orders = {}  # {price: {'client_order_index': int, 'is_ask': bool, 'base_amount': int}}
        self.total_profit = 0.0
        self.trades_count = 0
        self.total_volume = 0.0

    async def init(self):
        # Initialize Signer Client using shared utility
        self.client = await get_client()
        
        # Reuse internal clients
        self.api_client = self.client.api_client
        self.order_api = self.client.order_api
        self.account_api = lighter.AccountApi(self.api_client)

        err = self.client.check_client()
        if err:
            raise Exception(f"Client error: {err}")

        logger.info(f"✅ Connected to Lighter")
        logger.info(f"   Account: {self.client.account_index}")

        # Fetch next nonce
        self.order_index = await self.get_next_nonce()
        logger.info(f"   Next Nonce: {self.order_index}")

        # Cancel all existing orders to start fresh
        await self.cancel_all_open_orders()

    async def cancel_all_open_orders(self):
        """Cancel all open orders for this market"""
        try:
            print("   🧹 Cancelling all open orders...")
            
            # Generate auth token
            expiry = int(datetime.now().timestamp()) + 3600
            auth_token, err = self.client.create_auth_token_with_expiry(expiry)
            
            if err:
                logger.error(f"Failed to generate auth token for cancel: {err}")
                return

            # Get active orders
            orders = await self.order_api.account_active_orders(
                account_index=self.client.account_index,
                market_id=self.market_index,
                auth=auth_token
            )
            
            active_orders = orders.orders if hasattr(orders, 'orders') else []
            
            if not active_orders:
                print("   ✅ No open orders found.")
                return

            # Cancel each order
            count = 0
            for order in active_orders:
                # Assuming order has 'id' or 'order_id'
                order_id = getattr(order, 'order_id', None)
                if order_id:
                    tx, tx_hash, err = await cancel_order(
                        client=self.client,
                        market_index=int(self.market_index),
                        order_index=int(order_id)
                    )
                    if not err:
                        count += 1
                    else:
                        logger.warning(f"Failed to cancel order {order_id}: {err}")
                
                # Rate limit slightly
                if count % 5 == 0:
                    await asyncio.sleep(0.1)

            print(f"   ✅ Cancelled {count} old orders.")

        except Exception as e:
            logger.error(f"   ⚠️  Error cancelling orders: {e}")


    async def get_next_nonce(self):
        """Get next valid nonce from server using TransactionApi"""
        try:
            transaction_api = lighter.TransactionApi(self.api_client)
            nonce_data = await transaction_api.next_nonce(
                account_index=self.client.account_index,
                api_key_index=self.client.api_key_index
            )
            return int(nonce_data.nonce)
        except Exception as e:
            logger.warning(f"⚠️ Failed to get nonce via API: {e}")
            # Fallback to timestamp if API fails
            return int(datetime.now().timestamp() * 1000)

    async def calculate_grid_levels(self):
        # Fetch current market price
        order_book = await self.order_api.order_book_orders(market_id=self.market_index, limit=1)
        best_bid = float(order_book.bids[0].price)
        best_ask = float(order_book.asks[0].price)
        mid_price = (best_bid + best_ask) / 2

        spacing = (self.upper_price - self.lower_price) / (self.grid_count - 1)
        grid_levels = [self.lower_price + (i * spacing) for i in range(self.grid_count)]
        
        print(f"   {self.market_symbol} Market Price: ${mid_price:,.2f}")
        print(f"   Range: ${self.lower_price:,.2f} - ${self.upper_price:,.2f}")
        print(f"   Grids: {self.grid_count}")
        print(f"   Spacing: ${spacing:.4f}")

        self.spacing = spacing
        return spacing, grid_levels, mid_price

    async def place_grid_orders(self, grid_levels, mid_price):
        # Calculate fixed USD investment per grid
        self.usd_per_grid = (self.investment / self.grid_count)

        orders_placed = {'buy': 0, 'sell': 0}

        print(f"\n📝 Placing Grid Orders...")
        print(f"   Target Value per Grid: ${self.usd_per_grid:.2f}")

        for i, price in enumerate(grid_levels, 1):
            # Calculate coin amount dynamically for this specific price (Fixed Notional)
            # Investment is Margin, so Position = Margin * Leverage
            coin_amount = (self.usd_per_grid * self.leverage) / price
            multiplier = get_size_multiplier(self.market_symbol)
            base_amount = int(coin_amount * multiplier)

            is_ask = price > mid_price
            
            # Directional Logic: Only place orders that align with strategy
            # LONG: Only Buy initially (wait for fill to Sell)
            if self.direction == "LONG" and is_ask:
                continue
            # SHORT: Only Sell initially (wait for fill to Buy)
            if self.direction == "SHORT" and not is_ask:
                continue

            price_int = price_to_int(price, self.market_symbol)

            try:
                tx, tx_hash, err = await place_limit_order(
                    client=self.client,
                    market_index=self.market_index,
                    client_order_index=self.order_index,
                    base_amount=base_amount,
                    price_int=price_int,
                    is_ask=is_ask
                )

                if not err:
                    self.grid_orders[price] = {
                        'client_order_index': self.order_index,
                        'is_ask': is_ask,
                        'base_amount': base_amount,
                        'price_int': price_int,
                        'placed_at': time.time()
                    }
                    orders_placed['sell' if is_ask else 'buy'] += 1
                    self.order_index += 1
                    if i % 5 == 0 or i <= 3:
                        print(f"   ✓ {'SELL' if is_ask else 'BUY'} @ ${price:,.2f}")
                else:
                    if i <= 3:
                        print(f"   ✗ {'SELL' if is_ask else 'BUY'} @ ${price:,.2f} - {str(err)}")
                
                await asyncio.sleep(0.2) # Reduced delay

            except Exception as e:
                if i <= 3:
                    print(f"   ✗ Error at ${price:,.2f}: {str(e)}")

        print(f"\n✅ Grid Complete: {orders_placed['buy']} buy, {orders_placed['sell']} sell")
        return orders_placed

    async def get_active_orders(self):
        """Get active orders using OrderApi"""
        try:
            # Generate auth token
            expiry = int(datetime.now().timestamp()) + 3600
            auth_token, err = self.client.create_auth_token_with_expiry(expiry)
            if err:
                logger.error(f"Failed to generate auth token: {err}")
                return None

            orders = await self.order_api.account_active_orders(
                account_index=self.client.account_index,
                market_id=self.market_index,
                auth=auth_token
            )
            return orders.orders if hasattr(orders, 'orders') else []
        except Exception as e:
            logger.error(f"   ⚠️  Error getting orders: {e}")
            return None

    async def monitor_and_refill(self):
        """Monitor orders and auto-refill"""
        print(f"\n🔄 Auto-Refill Mode Started")
        
        check_interval = 2

        while self.running:
            try:
                # Sync nonce occasionally
                if self.trades_count % 10 == 0:
                    self.order_index = await self.get_next_nonce()

                # Get current price for display
                order_book = await self.order_api.order_book_orders(market_id=self.market_index, limit=1)
                best_bid = float(order_book.bids[0].price)
                best_ask = float(order_book.asks[0].price)
                current_price = (best_bid + best_ask) / 2
                print(f"   📊 Current Price: ${current_price:,.2f}")

                active_orders = await self.get_active_orders()
                if active_orders is None:
                    print("   ⚠️  Failed to fetch active orders, skipping cycle.")
                    await asyncio.sleep(check_interval)
                    continue

                if len(active_orders) >= self.grid_count + 2:
                    print(f"   ⚠️  Too many active orders ({len(active_orders)}/{self.grid_count}), skipping refill to prevent spam.")
                    await asyncio.sleep(check_interval)
                    continue

                active_prices = set()

                for order in active_orders:
                    # Parse price from order object
                    price_val = order.price if hasattr(order, 'price') else order.get('price', '0')
                    
                    # Dynamic precision handling
                    precision = PRICE_PRECISIONS.get(self.market_symbol, 1)
                    factor = 10 ** precision
                    price_float = float(price_val) / factor
                    # print(f"DEBUG: {price_val} -> {price_float}")
                    active_prices.add(round(price_float, precision))

                # Check for filled orders
                filled_prices = []
                for grid_price in list(self.grid_orders.keys()):
                    # Check if order is active
                    precision = PRICE_PRECISIONS.get(self.market_symbol, 1)
                    if round(grid_price, precision) not in active_prices:
                        # Check grace period (e.g. 10 seconds) to allow API propagation
                        order_info = self.grid_orders[grid_price]
                        if time.time() - order_info.get('placed_at', 0) < 10:
                            continue

                        filled_prices.append(grid_price)

                for price in filled_prices:
                    if price not in self.grid_orders: continue
                    
                    order_info = self.grid_orders[price]
                    was_ask = order_info['is_ask']
                    
                    multiplier = get_size_multiplier(self.market_symbol)
                    coin_amount = order_info['base_amount'] / multiplier
                    volume_usd = coin_amount * price
                    self.total_volume += volume_usd
                    self.trades_count += 1

                    # Log the trade
                    if was_ask:
                        profit = (price - self.lower_price) * 0.001 # Estimate
                        self.total_profit += profit
                        print(f"   💰 SELL @ ${price:,.2f} | Vol: ${volume_usd:.0f}")
                    else:
                        print(f"   📈 BUY @ ${price:,.2f} | Vol: ${volume_usd:.0f}")

                    del self.grid_orders[price]

                    # Standard Grid Logic: Place opposite order at next level
                    if was_ask:
                        # Sell filled -> Place Buy at lower price
                        new_price = price - self.spacing
                        new_is_ask = False
                    else:
                        # Buy filled -> Place Sell at higher price
                        new_price = price + self.spacing
                        new_is_ask = True
                    
                    # Check bounds
                    if new_price < self.lower_price * 0.99 or new_price > self.upper_price * 1.01:
                        print(f"   ⚠️  Target {new_price:,.2f} out of bounds, stopping chain.")
                        continue

                    # Check if active
                    precision = PRICE_PRECISIONS.get(self.market_symbol, 1)
                    if round(new_price, precision) in active_prices:
                        print(f"   ⚠️  Order at {new_price:,.2f} already active, skipping.")
                        continue

                    # Recalculate amount
                    multiplier = get_size_multiplier(self.market_symbol)
                    amount = int(((self.usd_per_grid * self.leverage) / new_price) * multiplier)
                    await self.refill_order(new_price, new_is_ask, amount)

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"   ⚠️  Monitor error: {e}")
                await asyncio.sleep(check_interval)

    async def refill_order(self, price, is_ask, base_amount):
        """Place a new order to replace the filled one"""
        try:
            price_int = price_to_int(price, self.market_symbol)

            tx, tx_hash, err = await place_limit_order(
                client=self.client,
                market_index=self.market_index,
                client_order_index=self.order_index,
                base_amount=base_amount,
                price_int=price_int,
                is_ask=is_ask
            )

            if err and "nonce" in str(err).lower():
                logger.warning(f"   ⚠️  Nonce error, resyncing...")
                self.order_index = await self.get_next_nonce()
                # Retry once
                tx, tx_hash, err = await place_limit_order(
                    client=self.client,
                    market_index=self.market_index,
                    client_order_index=self.order_index,
                    base_amount=base_amount,
                    price_int=price_int,
                    is_ask=is_ask
                )

            if not err:
                self.grid_orders[price] = {
                    'client_order_index': self.order_index,
                    'is_ask': is_ask,
                    'base_amount': base_amount,
                    'price_int': price_int,
                    'placed_at': time.time()
                }
                self.order_index += 1
                print(f"   ✅ Refilled {'SELL' if is_ask else 'BUY'} @ ${price:,.2f}")
            else:
                logger.error(f"   ⚠️  Refill failed @ ${price:,.2f}: {err}")

        except Exception as e:
            logger.error(f"   ❌ Refill error: {e}")

    def stop_bot(self, signum=None, frame=None):
        print(f"\n\n⏹️  Stopping bot...")
        print(f"📊 Final Stats:")
        print(f"   Total Trades: {self.trades_count}")
        print(f"   Total Volume: ${self.total_volume:.2f}")
        print(f"   Total Profit: ${self.total_profit:.2f}")
        self.running = False

    async def run(self):
        signal.signal(signal.SIGINT, self.stop_bot)

        try:
            print("=" * 60)
            print(f"🤖 Lighter Auto Grid Trading Bot")
            print("=" * 60)
            
            await self.init()
            
            spacing, grid_levels, mid_price = await self.calculate_grid_levels()
            await self.place_grid_orders(grid_levels, mid_price)
            await self.monitor_and_refill()

        except KeyboardInterrupt:
            self.stop_bot()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        finally:
            if self.client:
                await self.client.close()
            if self.api_client:
                await self.api_client.close()
            print("\n👋 Bot stopped successfully")

async def run_grid(token, direction, leverage, grid_count, investment, lower_price, upper_price):
    bot = GridTradingBot(token, direction, leverage, grid_count, investment, lower_price, upper_price)
    await bot.run()

if __name__ == "__main__":
    bot = GridTradingBot()
    asyncio.run(bot.run())
