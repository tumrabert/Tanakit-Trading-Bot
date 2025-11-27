import sys
import asyncio
import argparse
from lighter_tool.open_limit_order import main_test as test_limit_orders, open_limit_order
from grid_trading.bot import run_grid
from lighter_tool.upgrade_account_premium import main as upgrade_account
from lighter_tool.downgrade_account_standard import main as downgrade_account
from lighter_tool.markets import MARKETS

def main():
    parser = argparse.ArgumentParser(description="Lighter Trading Bot CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # limit_test
    subparsers.add_parser("limit_test", help="Run limit order verification suite")

    # grid
    grid_parser = subparsers.add_parser("grid", help="Start the neutral grid trading bot")
    grid_parser.add_argument("--token", type=str, default="BTC", help="Token symbol")
    grid_parser.add_argument("--direction", type=str, default="NEUTRAL", help="Market Direction")
    grid_parser.add_argument("--leverage", type=int, default=10, help="Leverage")
    grid_parser.add_argument("--grids", type=int, default=20, help="Grid Count")
    grid_parser.add_argument("--invest", type=float, default=100, help="Investment USD")
    grid_parser.add_argument("--lower", type=float, default=90000, help="Lower Price")
    grid_parser.add_argument("--upper", type=float, default=110000, help="Upper Price")

    # upgrade
    subparsers.add_parser("upgrade", help="Upgrade account to Premium")

    # downgrade
    subparsers.add_parser("downgrade", help="Downgrade account to Standard")

    # open_limit
    open_parser = subparsers.add_parser("open_limit", help="Open a limit order")
    open_parser.add_argument("token", type=str, help="Token symbol (BTC, ETH, etc.)")
    open_parser.add_argument("side", type=str, choices=["Long", "Short"], help="Side")
    open_parser.add_argument("amount", type=float, help="Margin Amount in USD")
    open_parser.add_argument("price", type=float, help="Limit Price")
    open_parser.add_argument("--leverage", type=int, default=1, help="Leverage (default: 1)")
    open_parser.add_argument("--tp", type=float, help="Take Profit Price")
    open_parser.add_argument("--sl", type=float, help="Stop Loss Price")

    args = parser.parse_args()

    if args.command == "limit_test":
        print("Running Limit Order Tests...")
        asyncio.run(test_limit_orders())
    elif args.command == "grid":
        print("Starting Grid Bot...")
        asyncio.run(run_grid(
            token=args.token,
            direction=args.direction,
            leverage=args.leverage,
            grid_count=args.grids,
            investment=args.invest,
            lower_price=args.lower,
            upper_price=args.upper
        ))
    elif args.command == "upgrade":
        print("Upgrading Account...")
        asyncio.run(upgrade_account())
    elif args.command == "downgrade":
        print("Downgrading Account...")
        asyncio.run(downgrade_account())
    elif args.command == "open_limit":
        print(f"Opening {args.side} {args.token} order...")
        asyncio.run(open_limit_order(
            token=args.token,
            leverage=args.leverage,
            side=args.side,
            amount_in_usd=args.amount,
            price=args.price,
            take_profit_price=args.tp,
            stop_loss_price=args.sl
        ))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
