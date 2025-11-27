import lighter
import asyncio
import logging

logger = logging.getLogger(__name__)

async def place_limit_order(client, market_index, base_amount, price_int, is_ask, client_order_index=0, reduce_only=False):
    """
    Places a simple limit order using the provided client.
    Returns (tx, tx_hash, err).
    """
    tx, tx_hash, err = await client.create_order(
        market_index=market_index,
        client_order_index=client_order_index,
        base_amount=base_amount,
        price=price_int,
        is_ask=is_ask,
        order_type=lighter.SignerClient.ORDER_TYPE_LIMIT,
        time_in_force=lighter.SignerClient.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
        reduce_only=reduce_only,
        trigger_price=0
    )
    return tx, tx_hash, err

async def cancel_order(client, market_index, order_index):
    """
    Cancels an order by its order index (ID).
    Returns (tx, tx_hash, err).
    """
    tx, tx_hash, err = await client.cancel_order(
        market_index=market_index,
        order_index=order_index
    )
    return tx, tx_hash, err
