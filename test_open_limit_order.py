import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
import asyncio

# Add project directory to path to import open_limit_order
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_limit_order import open_limit_order, MARKETS
import lighter

class TestOpenLimitOrder(unittest.IsolatedAsyncioTestCase):
    
    @patch('open_limit_order.get_client')
    @patch('open_limit_order.get_market_price')
    async def test_open_long_limit_order(self, mock_get_market_price, mock_get_client):
        # Setup Mock
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_get_market_price.return_value = (50000.0, 50010.0) # Bid, Ask
        
        # Mock create_order return
        mock_client.create_order.return_value = ("tx_info", "0x123hash", None)
        
        # Execute
        token = "BTC"
        leverage = 10
        amount_usd = 100
        price = 50000
        # Expected calculation:
        # Position = 100 * 10 = 1000 USD
        # Coin Amount = 1000 / 50000 = 0.02 BTC
        # Base Amount = 0.02 * 1e5 = 2000
        # Price Int = 50000.0 -> 500000
        
        await open_limit_order(token, leverage, "Long", amount_usd, price)
        
        # Verify
        mock_client.create_order.assert_called_once()
        call_args = mock_client.create_order.call_args
        _, kwargs = call_args
        
        self.assertEqual(kwargs['is_ask'], 0, "Long should be is_ask=0") 
        self.assertEqual(kwargs['price'], 500000, "Price should be converted to int representation")
        self.assertEqual(kwargs['base_amount'], 2000, "Base amount calculation incorrect")
        self.assertEqual(kwargs['reduce_only'], 0)

    @patch('open_limit_order.get_client')
    @patch('open_limit_order.get_market_price')
    async def test_open_short_limit_order(self, mock_get_market_price, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_get_market_price.return_value = (50000.0, 50010.0)
        mock_client.create_order.return_value = ("tx_info", "0x123hash", None)
        
        await open_limit_order("BTC", 10, "Short", 100, 50000)
        
        _, kwargs = mock_client.create_order.call_args
        self.assertEqual(kwargs['is_ask'], 1, "Short should be is_ask=1")

    @patch('open_limit_order.get_client')
    @patch('open_limit_order.get_market_price')
    async def test_open_order_with_tp_sl(self, mock_get_market_price, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_get_market_price.return_value = (50000.0, 50010.0)
        mock_client.create_grouped_orders.return_value = "0xGroupedHash"
        
        await open_limit_order("BTC", 10, "Long", 100, 50000, take_profit_price=55000, stop_loss_price=45000)
        
        # Should call create_grouped_orders instead of create_order
        mock_client.create_order.assert_not_called()
        mock_client.create_grouped_orders.assert_called_once()
        
        _, kwargs = mock_client.create_grouped_orders.call_args
        self.assertEqual(kwargs['grouping_type'], lighter.SignerClient.GROUPING_TYPE_ONE_TRIGGERS_A_ONE_CANCELS_THE_OTHER)
        self.assertEqual(len(kwargs['orders']), 3, "Should have 3 orders: Main, TP, SL")
        
        # Verify Order Types
        main_order = kwargs['orders'][0]
        tp_order = kwargs['orders'][1]
        sl_order = kwargs['orders'][2]
        
        self.assertEqual(main_order.Type, lighter.SignerClient.ORDER_TYPE_LIMIT)
        self.assertEqual(tp_order.Type, lighter.SignerClient.ORDER_TYPE_TAKE_PROFIT_LIMIT)
        self.assertEqual(sl_order.Type, lighter.SignerClient.ORDER_TYPE_STOP_LOSS_LIMIT)

    @patch('open_limit_order.get_client')
    async def test_invalid_token(self, mock_get_client):
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        with self.assertRaises(ValueError):
            await open_limit_order("INVALID_TOKEN", 10, "Long", 100, 50000)

if __name__ == '__main__':
    unittest.main()
