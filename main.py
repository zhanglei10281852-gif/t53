import argparse
import sys
from datetime import date

from rich.console import Console

from calculator import (
    read_inventory,
    enrich_inventory_items,
    validate_inventory,
)
from reporter import generate_report, print_alert_terminal

console = Console()


def cmd_check(args):
    errors = validate_inventory(args.input)
    if not errors:
        console.print("[green]数据校验通过，未发现错误[/green]")
        return 0

    console.print(f"[red]发现 {len(errors)} 个错误：[/red]")
    console.print("-" * 60)
    for err in errors:
        console.print(f"  第{err.row_number}行 - [{err.field}]: {err.message}")
    return 1


def cmd_report(args):
    errors = validate_inventory(args.input)
    if errors:
        console.print(f"[red]数据校验失败，发现 {len(errors)} 个错误，请先修正数据。[/red]")
        console.print(f"使用 `python main.py check --input {args.input}` 查看详情。")
        return 1

    items = read_inventory(args.input)
    today = date.today()
    enriched_items = enrich_inventory_items(items, today)
    generate_report(enriched_items, args.output, today)

    product_count = len(set(item.name for item in enriched_items))
    batch_count = len(enriched_items)
    total_value = sum(item.total_value for item in enriched_items)

    console.print(f"[green]报告已生成: {args.output}[/green]")
    console.print(f"  - 品种总数: {product_count}")
    console.print(f"  - 批次总数: {batch_count}")
    console.print(f"  - 总金额: {total_value:.2f} 元")
    return 0


def cmd_alert(args):
    errors = validate_inventory(args.input)
    if errors:
        console.print(f"[red]数据校验失败，发现 {len(errors)} 个错误，请先修正数据。[/red]")
        return 1

    items = read_inventory(args.input)
    today = date.today()
    enriched_items = enrich_inventory_items(items, today)
    print_alert_terminal(enriched_items)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="中药房库存盘点与效期管理工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    check_parser = subparsers.add_parser("check", help="数据校验")
    check_parser.add_argument("--input", required=True, help="输入CSV文件路径")
    check_parser.set_defaults(func=cmd_check)

    report_parser = subparsers.add_parser("report", help="生成Excel报告")
    report_parser.add_argument("--input", required=True, help="输入CSV文件路径")
    report_parser.add_argument(
        "--output", default="report.xlsx", help="输出Excel文件路径"
    )
    report_parser.set_defaults(func=cmd_report)

    alert_parser = subparsers.add_parser("alert", help="终端预警输出")
    alert_parser.add_argument("--input", required=True, help="输入CSV文件路径")
    alert_parser.set_defaults(func=cmd_alert)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
