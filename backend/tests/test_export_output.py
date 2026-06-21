#!/usr/bin/env python3
"""
نمونه خروجی Decision Engine

این اسکریپت نحوه استفاده از Decision Engine و خروجی‌های آن را نشان می‌دهد.

نویسنده: MT5 Trading Team
"""

import sys
import json
from datetime import datetime
sys.path.insert(0, "/tmp/cc-agent/67916392/project")

from backend.analysis.decision_engine import (
    DecisionEngine,
    DecisionInput,
    SMCContext,
    PriceActionContext,
    SessionContext,
    LicenseContext,
    RiskContext,
    SymbolPolicy,
    VolatilityContext
)
from backend.core.enums import (
    MarketTrend,
    DecisionDirection,
    SessionType
)


def print_separator(title: str) -> None:
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def example_buy_decision():
    """مثال تصمیم خرید"""
    print_separator("مثال 1: تصمیم خرید (BUY)")

    engine = DecisionEngine()

    # ایجاد ورودی با سیگنال‌های صعودی قوی
    input_data = DecisionInput(
        symbol="EURUSD",
        timeframe="H1",
        current_price=1.0850,
        smc_context=SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=80,
            structure_event="BOS",
            structure_direction="bullish",
            structure_level=1.0860,
            liquidity_swept=True,
            liquidity_direction="bullish",
            premium_discount="discount",
            order_blocks=[{"type": "OB", "direction": "bullish", "active": True}],
            fvgs=[{"type": "bullish", "fill_percent": 25}]
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.BULLISH,
            direction_score=75,
            patterns=[
                {"name": "engulfing", "direction": "bullish", "score": 15},
                {"name": "pin_bar", "direction": "bullish", "score": 12}
            ]
        ),
        session_context=SessionContext(
            current_session=SessionType.LONDON,
            killzone_active=True,
            killzone_name="London",
            session_score=85
        ),
        license_context=LicenseContext(
            is_valid=True,
            is_expired=False,
            license_type="pro"
        ),
        risk_context=RiskContext(
            daily_pnl=100.0,
            daily_trades=2,
            open_positions=1,
            max_daily_loss=-500.0,
            max_daily_trades=5,
            max_positions=3
        ),
        symbol_policy=SymbolPolicy(
            symbol="EURUSD",
            allowed=True
        ),
        volatility_context=VolatilityContext(atr=0.0020)
    )

    # تصمیم‌گیری
    result = engine.make_decision(input_data)

    # نمایش نتیجه
    print(f"\n📊 نماد: {result.symbol}")
    print(f"📅 تایم‌فریم: {result.timeframe}")
    print(f"⏰ زمان: {result.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🎯 تصمیم: {result.decision.value}")
    print(f"📍 جهت: {result.direction.value}")
    print(f"💯 امتیاز کیفیت: {result.quality_score}")
    print(f"📈 امتیاز اعتماد: {result.confidence_score}")
    print(f"✅ مجاز: {result.allowed}")

    if result.trading_levels:
        print(f"\n💰 سطوح معاملاتی:")
        print(f"   Entry: {result.trading_levels.entry_zone:.5f}")
        print(f"   Stop Loss: {result.trading_levels.stop_loss:.5f}")
        print(f"   Take Profit 1: {result.trading_levels.take_profit_1:.5f}")
        print(f"   Take Profit 2: {result.trading_levels.take_profit_2:.5f if result.trading_levels.take_profit_2 else 'N/A'}")
        print(f"   R:R Ratio: {result.trading_levels.risk_reward_ratio:.2f}")

    print(f"\n📝 دلایل:")
    for reason in result.reasons_persian[:5]:
        print(f"   • {reason}")

    print(f"\n📊 Breakdown امتیازها:")
    for component, score in result.score_breakdown.items():
        if score > 0:
            print(f"   {component}: {score}")

    return result


def example_sell_decision():
    """مثال تصمیم فروش"""
    print_separator("مثال 2: تصمیم فروش (SELL)")

    engine = DecisionEngine()

    input_data = DecisionInput(
        symbol="GBPUSD",
        timeframe="H4",
        current_price=1.2650,
        smc_context=SMCContext(
            trend=MarketTrend.BEARISH,
            trend_score=75,
            structure_event="CHOCH",
            structure_direction="bearish",
            structure_level=1.2640,
            liquidity_swept=True,
            liquidity_direction="bearish",
            premium_discount="premium",
            order_blocks=[{"type": "OB", "direction": "bearish", "active": True}]
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.BEARISH,
            direction_score=70,
            patterns=[
                {"name": "engulfing", "direction": "bearish", "score": 15}
            ]
        ),
        session_context=SessionContext(
            current_session=SessionType.NEW_YORK,
            killzone_active=True,
            killzone_name="New York",
            session_score=80
        ),
        license_context=LicenseContext(is_valid=True, is_expired=False),
        risk_context=RiskContext(daily_pnl=0, daily_trades=0, open_positions=0),
        symbol_policy=SymbolPolicy(symbol="GBPUSD", allowed=True),
        volatility_context=VolatilityContext(atr=0.0030)
    )

    result = engine.make_decision(input_data)

    print(f"\n📊 نماد: {result.symbol}")
    print(f"🎯 تصمیم: {result.decision.value}")
    print(f"📍 جهت: {result.direction.value}")
    print(f"💯 امتیاز: {result.quality_score}")

    if result.trading_levels:
        print(f"\n💰 سطوح:")
        print(f"   Entry: {result.trading_levels.entry_zone:.5f}")
        print(f"   SL: {result.trading_levels.stop_loss:.5f}")
        print(f"   TP: {result.trading_levels.take_profit_1:.5f}")

    return result


def example_no_trade_low_quality():
    """مثال عدم معامله - کیفیت پایین"""
    print_separator("مثال 3: عدم معامله - کیفیت پایین")

    engine = DecisionEngine()

    input_data = DecisionInput(
        symbol="USDJPY",
        timeframe="M15",
        current_price=149.50,
        smc_context=SMCContext(
            trend=MarketTrend.RANGING,
            trend_score=20,
            structure_event=None,
            structure_direction=None,
            structure_level=None,
            liquidity_swept=False,
            liquidity_direction=None,
            premium_discount="neutral"
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.NEUTRAL,
            direction_score=10,
            patterns=[]
        ),
        session_context=SessionContext(
            current_session=SessionType.CLOSED,
            killzone_active=False,
            session_score=5
        )
    )

    result = engine.make_decision(input_data)

    print(f"\n📊 نماد: {result.symbol}")
    print(f"🎯 تصمیم: {result.decision.value}")
    print(f"💯 امتیاز: {result.quality_score}")
    print(f"\n📝 دلایل:")
    for reason in result.reasons_persian:
        print(f"   • {reason}")

    return result


def example_no_trade_conflict():
    """مثال عدم معامله - تعارض"""
    print_separator("مثال 4: عدم معامله - تعارض سیگنال‌ها")

    engine = DecisionEngine()

    # SMC صعودی ولی PA نزولی
    input_data = DecisionInput(
        symbol="XAUUSD",
        timeframe="H1",
        current_price=1950.0,
        smc_context=SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=50,  # امتیاز متوسط
            structure_event="CHOCH",
            structure_direction="bullish",
            structure_level=1955.0,
            liquidity_swept=False,
            liquidity_direction=None,
            premium_discount="neutral"
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.BEARISH,  # مخالف SMC
            direction_score=50,
            patterns=[
                {"name": "engulfing", "direction": "bearish", "score": 15}
            ]
        ),
        session_context=SessionContext(
            current_session=SessionType.LONDON,
            killzone_active=True,
            session_score=70
        )
    )

    result = engine.make_decision(input_data)

    print(f"\n📊 نماد: {result.symbol}")
    print(f"🎯 تصمیم: {result.decision.value}")
    print(f"💯 امتیاز: {result.quality_score}")
    print(f"\n📝 دلایل:")
    for reason in result.reasons_persian:
        print(f"   • {reason}")

    if result.metadata.get("conflict"):
        print("\n⚠️ تعارض بین سیگنال‌ها شناسایی شد!")

    return result


def example_blocked_license():
    """مثال بلاک - لایسنس نامعتبر"""
    print_separator("مثال 5: بلاک - لایسنس نامعتبر")

    engine = DecisionEngine()

    input_data = DecisionInput(
        symbol="EURUSD",
        timeframe="H1",
        current_price=1.0850,
        smc_context=SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=80,
            structure_event="BOS",
            structure_direction="bullish",
            structure_level=1.0860,
            liquidity_swept=True,
            liquidity_direction="bullish",
            premium_discount="discount"
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.BULLISH,
            direction_score=75,
            patterns=[{"name": "engulfing", "direction": "bullish", "score": 15}]
        ),
        session_context=SessionContext(
            current_session=SessionType.LONDON,
            killzone_active=True,
            session_score=80
        ),
        license_context=LicenseContext(
            is_valid=False,  # لایسنس نامعتبر
            is_expired=False,
            license_type="trial"
        ),
        symbol_policy=SymbolPolicy(symbol="EURUSD", allowed=True)
    )

    result = engine.make_decision(input_data)

    print(f"\n📊 نماد: {result.symbol}")
    print(f"🎯 تصمیم: {result.decision.value}")
    print(f"✅ مجاز: {result.allowed}")
    print(f"\n🚫 دلایل بلاک:")
    for reason in result.blocked_reasons:
        print(f"   • {reason.value}")
    print(f"\n📝 توضیح فارسی:")
    for reason in result.reasons_persian:
        print(f"   • {reason}")

    return result


def example_blocked_risk():
    """مثال بلاک - حد ضرر روزانه"""
    print_separator("مثال 6: بلاک - حد ضرر روزانه")

    engine = DecisionEngine()

    input_data = DecisionInput(
        symbol="EURUSD",
        timeframe="H1",
        current_price=1.0850,
        smc_context=SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=80,
            structure_event="BOS",
            structure_direction="bullish",
            structure_level=1.0860,
            liquidity_swept=True,
            liquidity_direction="bullish",
            premium_discount="discount"
        ),
        license_context=LicenseContext(is_valid=True, is_expired=False),
        symbol_policy=SymbolPolicy(symbol="EURUSD", allowed=True),
        risk_context=RiskContext(
            daily_pnl=-600.0,  # زیان بیش از حد
            daily_trades=3,
            open_positions=1,
            max_daily_loss=-500.0,
            max_daily_trades=5,
            max_positions=3
        )
    )

    result = engine.make_decision(input_data)

    print(f"\n📊 نماد: {result.symbol}")
    print(f"🎯 تصمیم: {result.decision.value}")
    print(f"✅ مجاز: {result.allowed}")
    print(f"\n🚫 دلایل بلاک:")
    for reason in result.blocked_reasons:
        print(f"   • {reason.value}")
    print(f"\n📝 توضیح فارسی:")
    for reason in result.reasons_persian:
        print(f"   • {reason}")

    return result


def example_json_output():
    """مثال خروجی JSON برای API"""
    print_separator("مثال 7: خروجی JSON برای API")

    engine = DecisionEngine()

    input_data = DecisionInput(
        symbol="EURUSD",
        timeframe="H1",
        current_price=1.0850,
        smc_context=SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=80,
            structure_event="BOS",
            structure_direction="bullish",
            structure_level=1.0860,
            liquidity_swept=True,
            liquidity_direction="bullish",
            premium_discount="discount"
        ),
        price_action_context=PriceActionContext(
            direction=DecisionDirection.BULLISH,
            direction_score=75,
            patterns=[{"name": "engulfing", "direction": "bullish", "score": 15}]
        ),
        session_context=SessionContext(
            current_session=SessionType.LONDON,
            killzone_active=True,
            session_score=80
        ),
        license_context=LicenseContext(is_valid=True, is_expired=False),
        symbol_policy=SymbolPolicy(symbol="EURUSD", allowed=True),
        volatility_context=VolatilityContext(atr=0.0020)
    )

    result = engine.make_decision(input_data)

    # تبدیل به دیکشنری برای JSON
    output_dict = {
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "created_at": result.created_at.isoformat(),
        "decision": result.decision.value,
        "direction": result.direction.value,
        "confidence_score": result.confidence_score,
        "quality_score": result.quality_score,
        "allowed": result.allowed,
        "reason_codes": [r.value for r in result.reason_codes],
        "reasons": result.reasons_persian,
        "trading_levels": {
            "entry": result.trading_levels.entry_zone if result.trading_levels else None,
            "stop_loss": result.trading_levels.stop_loss if result.trading_levels else None,
            "take_profit_1": result.trading_levels.take_profit_1 if result.trading_levels else None,
            "take_profit_2": result.trading_levels.take_profit_2 if result.trading_levels else None,
            "take_profit_3": result.trading_levels.take_profit_3 if result.trading_levels else None,
            "invalidation": result.trading_levels.invalidation_level if result.trading_levels else None,
            "risk_reward": result.trading_levels.risk_reward_ratio if result.trading_levels else None
        },
        "score_breakdown": result.score_breakdown,
        "metadata": result.metadata
    }

    print("\n📤 خروجی JSON:")
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))

    return result


def main():
    """اجرای همه مثال‌ها"""
    print("=" * 60)
    print(" 📊 نمونه خروجی Decision Engine")
    print(" MT5 Trading System")
    print("=" * 60)

    # اجرای مثال‌ها
    example_buy_decision()
    example_sell_decision()
    example_no_trade_low_quality()
    example_no_trade_conflict()
    example_blocked_license()
    example_blocked_risk()
    example_json_output()

    print("\n" + "=" * 60)
    print(" 🏁 پایان نمونه‌ها")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
