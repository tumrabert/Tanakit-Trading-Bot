"""
Lighter Market Making Bot (Volume Generator)
Strategy: Place BUY + SELL orders simultaneously with small spread
High-frequency trading for maximum volume
"""
import asyncio
import os
import signal
import logging
from datetime import datetime
from dotenv import load_dotenv
import lighter

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class MarketMakerBot:
    # Market symbols
    MARKETS = {
        0: "ETH", 1: "BTC", 2: "SOL", 3: "DOGE", 4: "1000PEPE",
        5: "WIF", 6: "WLD", 7: "XRP", 8: "LINK", 9: "AVAX"
    }

    def __init__(self):
        self.api_key_pk = os.getenv('API_KEY_PRIVATE_KEY')
        self.account_index = int(os.getenv('ACCOUNT_INDEX'))
        self.api_key_index = int(os.getenv('API_KEY_INDEX'))
        self.base_url = os.getenv('BASE_URL')
        self.market_index = int(os.getenv('MARKET_INDEX', 1))
        self.leverage = int(os.getenv('LEVERAGE', 5))
        self.spread_percent = float(os.getenv('SPREAD_PERCENT', 0.05))  # 0.05% spread
        self.order_size_usd = float(os.getenv('ORDER_SIZE_USDC', 20))  # $20 per order

        self.client = None
        self.api_client = None
        self.order_api = None
        self.account_api = None
        self.transaction_api = None

        self.order_index = 0
        self.market_symbol = self.MARKETS.get(self.market_index, f"Market{self.market_index}")

        # Tracking
        self.running = True
        self.total_volume = 0.0
        self.trades_count = 0
        self.profit = 0.0
        
        # Track active orders: { 'buy': {'id': int, 'price': float}, 'sell': {'id': int, 'price': float} }
        self.active_orders_map = {'buy': None, 'sell': None}

    async def init(self):
        self.client = lighter.SignerClient(
            url=self.base_url,
            private_key=self.api_key_pk,
            account_index=self.account_index,
            api_key_index=self.api_key_index
        )

        self.api_client = lighter.ApiClient(
            configuration=lighter.Configuration(host=self.base_url)
        )
        self.order_api = lighter.OrderApi(self.api_client)
        self.account_api = lighter.AccountApi(self.api_client)
        self.transaction_api = lighter.TransactionApi(self.api_client)

        err = self.client.check_client()
        if err:
            raise Exception(f"Client error: {err}")

        logger.info(f"✅ Connected to Lighter")
        logger.info(f"   Account: {self.account_index}")

        # Fetch next nonce
        self.order_index = await self.get_next_nonce()
        logger.info(f"   Next Nonce: {self.order_index}")

    async def get_current_price(self):
        """Get current market price via OrderApi"""
        try:
            order_book = await self.order_api.order_book_details(market_id=self.market_index)
            if not order_book.asks or not order_book.bids:
                raise Exception("Empty order book")
                
            best_bid = float(order_book.bids[0].price)
            best_ask = float(order_book.asks[0].price)
            return (best_bid + best_ask) / 2
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            raise

    async def get_next_nonce(self):
        """Get next valid nonce from server"""
        try:
            nonce_data = await self.transaction_api.next_nonce(
                account_index=self.account_index,
                api_key_index=self.api_key_index
            )
            return int(nonce_data.nonce)
        except Exception as e:
            logger.warning(f"⚠️ Failed to get nonce: {e}")
            return int(datetime.now().timestamp() * 1000)

    def price_to_int(self, price_float):
        """Convert price to int format"""
        price_str = f"{price_float:.1f}"
        price_int = int(price_str.replace(".", ""))
        return price_int

    async def place_order(self, price, is_ask, base_amount):
        """Helper to place a single order"""
        price_int = self.price_to_int(price)
        
        tx, tx_hash, err = await self.client.create_order(
            market_index=self.market_index,
            client_order_index=self.order_index,
            base_amount=base_amount,
            price=price_int,
            is_ask=is_ask,
            order_type=lighter.SignerClient.ORDER_TYPE_LIMIT,
            time_in_force=lighter.SignerClient.ORDER_TIME_IN_FORCE_POST_ONLY,
            reduce_only=False,
            trigger_price=0
        )

        # Retry on nonce error
        if err and "nonce" in str(err).lower():
            logger.warning(f"   ⚠️  Nonce error ({'SELL' if is_ask else 'BUY'}), resyncing...")
            self.order_index = await self.get_next_nonce()
            tx, tx_hash, err = await self.client.create_order(
                market_index=self.market_index,
                client_order_index=self.order_index,
                base_amount=base_amount,
                price=price_int,
                is_ask=is_ask,
                order_type=lighter.SignerClient.ORDER_TYPE_LIMIT,
                time_in_force=lighter.SignerClient.ORDER_TIME_IN_FORCE_POST_ONLY,
                reduce_only=False,
                trigger_price=0
            )

        if not err:
            order_id = self.order_index
            self.order_index += 1
            return order_id
        else:
            logger.error(f"   ❌ {'SELL' if is_ask else 'BUY'} failed: {err}")
            return None

    async def cancel_order(self, order_id):
        """Cancel a specific order"""
        try:
            tx, tx_hash, err = await self.client.cancel_order(
                market_index=self.market_index,
                order_index=order_id
            )
            if err:
                logger.error(f"   ❌ Cancel failed for order {order_id}: {err}")
            else:
                logger.info(f"   🗑️  Cancelled order {order_id}")
        except Exception as e:
            logger.error(f"   ❌ Cancel error: {e}")

    async def place_market_making_orders(self):
        """Place BUY + SELL orders simultaneously with spread"""
        try:
            current_price = await self.get_current_price()

            # Calculate spread prices
            spread_amount = current_price * (self.spread_percent / 100)
            buy_price = current_price - spread_amount
            sell_price = current_price + spread_amount

            # Calculate order size
            coin_amount = (self.order_size_usd * self.leverage) / current_price
            base_amount = int(coin_amount * 1e8)

            print(f"\n💱 Market Price: ${current_price:,.2f}")
            print(f"   Spread: {self.spread_percent}%")
            print(f"   BUY  @ ${buy_price:,.2f}")
            print(f"   SELL @ ${sell_price:,.2f}")

            # Place BUY
            buy_id = await self.place_order(buy_price, False, base_amount)
            if buy_id:
                self.active_orders_map['buy'] = {'id': buy_id, 'price': buy_price}
                print(f"   ✅ BUY order placed")

            await asyncio.sleep(0.2)

            # Place SELL
            sell_id = await self.place_order(sell_price, True, base_amount)
            if sell_id:
                self.active_orders_map['sell'] = {'id': sell_id, 'price': sell_price}
                print(f"   ✅ SELL order placed")

            return buy_price, sell_price

        except Exception as e:
            logger.error(f"   ⚠️  Error placing orders: {e}")
            return None, None

    async def get_active_orders(self):
        """Get active orders via AccountApi"""
        try:
            orders_data = await self.account_api.account_active_orders(
                account_index=self.account_index,
                market_id=self.market_index
            )
            return orders_data.orders if hasattr(orders_data, 'orders') else []
        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return []

    async def monitor_and_refill(self):
        """Monitor orders and refill when both sides fill"""
        print(f"\n🔄 Market Making Started")
        print(f"   Monitoring every 1 second (Ultra HFT)")
        
        # Place initial orders
        await self.place_market_making_orders()

        check_interval = 1

        while self.running:
            try:
                await asyncio.sleep(check_interval)

                # Sync nonce occasionally
                if self.trades_count % 20 == 0:
                    self.order_index = await self.get_next_nonce()

                # Check active orders
                active_orders = await self.get_active_orders()
                
                # Extract client order IDs from active orders
                # Note: The SDK might return 'client_order_id' or 'order_id' (exchange id)
                # We need to verify what 'client_order_index' maps to in the response.
                # Usually it's 'client_order_id' or similar.
                active_client_ids = set()
                for o in active_orders:
                    # Assuming 'id' is the client order index or there is a field for it.
                    # If not, we might need to rely on price matching or exchange IDs if we tracked them.
                    # Lighter usually returns 'order_id' (exchange) and 'client_order_id'.
                    # Let's assume 'client_order_id' exists.
                    cid = getattr(o, 'client_order_id', None)
                    if cid is not None:
                        active_client_ids.add(int(cid))
                
                # Check status of our tracked orders
                buy_active = False
                sell_active = False
                
                if self.active_orders_map['buy']:
                    buy_id = self.active_orders_map['buy']['id']
                    if buy_id in active_client_ids:
                        buy_active = True
                
                if self.active_orders_map['sell']:
                    sell_id = self.active_orders_map['sell']['id']
                    if sell_id in active_client_ids:
                        sell_active = True

                # Logic:
                # 1. If BOTH are gone -> Both filled (ideal)
                # 2. If ONE is gone -> One filled, CANCEL the other immediately
                # 3. If BOTH active -> Do nothing (or update if price moved too much - not implemented yet)

                if not buy_active and not sell_active:
                    if self.active_orders_map['buy'] and self.active_orders_map['sell']:
                        # Both filled
                        volume = self.order_size_usd * 2
                        profit = (self.active_orders_map['sell']['price'] - self.active_orders_map['buy']['price']) * (self.order_size_usd / self.active_orders_map['buy']['price'])
                        
                        self.total_volume += volume
                        self.trades_count += 2
                        self.profit += profit
                        print(f"   💰 Both filled! Profit: ${profit:.2f} | Total Vol: ${self.total_volume:.0f}")
                    
                    # Reset and replace
                    self.active_orders_map['buy'] = None
                    self.active_orders_map['sell'] = None
                    await self.place_market_making_orders()

                elif not buy_active and sell_active:
                    # Buy filled, Sell still active
                    print(f"   📉 BUY filled! Cancelling SELL...")
                    self.total_volume += self.order_size_usd
                    self.trades_count += 1
                    
                    # Cancel SELL
                    if self.active_orders_map['sell']:
                        await self.cancel_order(self.active_orders_map['sell']['id'])
                    
                    self.active_orders_map['buy'] = None
                    self.active_orders_map['sell'] = None
                    await self.place_market_making_orders()

                elif buy_active and not sell_active:
                    # Sell filled, Buy still active
                    print(f"   📈 SELL filled! Cancelling BUY...")
                    self.total_volume += self.order_size_usd
                    self.trades_count += 1
                    
                    # Cancel BUY
                    if self.active_orders_map['buy']:
                        await self.cancel_order(self.active_orders_map['buy']['id'])

                    self.active_orders_map['buy'] = None
                    self.active_orders_map['sell'] = None
                    await self.place_market_making_orders()

            except Exception as e:
                logger.error(f"   ⚠️  Monitor error: {e}")
                await asyncio.sleep(check_interval)

    def stop_bot(self, signum=None, frame=None):
        print(f"\n\n⏹️  Stopping Market Maker...")
        print(f"📊 Final Stats:")
        print(f"   Total Trades: {self.trades_count}")
        print(f"   Total Volume: ${self.total_volume:.2f}")
        print(f"   Total Profit: ${self.profit:.2f}")
        self.running = False

    async def run(self):
        signal.signal(signal.SIGINT, self.stop_bot)

        try:
            print("=" * 60)
            print(f"💱 Lighter Market Making Bot")
            print("=" * 60)
            
            await self.init()
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
            print("\n👋 Market Maker stopped")

if __name__ == "__main__":
    bot = MarketMakerBot()
    asyncio.run(bot.run())
