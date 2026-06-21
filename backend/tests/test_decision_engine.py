"""
تست واحد موتور تصمیم‌گیری

شامل تست‌های کامل برای:
- تصمیم خرید (BUY)
- تصمیم فروش (SELL)
- عدم معامله (NO_TRADE)
- حل تعارض
- کیفیت پایین
- بلاک لایسنس
- بلاک ریسک

نویسنده: MT5 Trading Team
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from ..analysis.decision_engine import (
    DecisionEngine, DecisionInput, DecisionOutput,
    SMCContext, PriceActionContext, MultiTimeframeContext,
    SessionContext, LiquidityContext, VolatilityContext,
    RiskContext, LicenseContext, SymbolPolicy,
    TradingLevels, RiskProfile
)
from ..core.enums import (
    DecisionAction, DecisionDirection, DecisionQuality,
    DecisionConfidence, SignalStrength, MarketTrend,
    LiquidityState, SessionType, RiskLevel, ReasonCode, BlockReason
)


# =====================================================
# Fixtures
# =====================================================

@pytest.fixture
def engine():
    """ایجاد نمونه موتور تصمیم‌گیری"""
    return DecisionEngine()


@pytest.fixture
def base_input():
    """ورودی پایه برای تست‌ها"""
    return DecisionInput(
        symbol="EURUSD",
        timeframe="H1",
        current_price=1.0850
    )


@pytest.fixture
def bullish_smc_context():
    """زمینه SMC صعودی"""
    return SMCContext(
        trend=MarketTrend.BULLISH,
        trend_score=75,
        structure_event="BOS",
        structure_direction="bullish",
        structure_level=1.0860,
        liquidity_swept=True,
        liquidity_direction="bullish",
        premium_discount="discount",
        order_blocks=[{"type": "OB", "direction": "bullish", "active": True}],
        fvgs=[{"type": "bullish", "fill_percent": 30}],
        swing_high=1.0875,
        swing_low=1.0835
    )


@pytest.fixture
def bearish_smc_context():
    """زمینه SMC نزولی"""
    return SMCContext(
        trend=MarketTrend.BEARISH,
        trend_score=70,
        structure_event="CHOCH",
        structure_direction="bearish",
        structure_level=1.0840,
        liquidity_swept=True,
        liquidity_direction="bearish",
        premium_discount="premium",
        order_blocks=[{"type": "OB", "direction": "bearish", "active": True}],
        fvgs=[],
        swing_high=1.0875,
        swing_low=1.0835
    )


@pytest.fixture
def bullish_pa_context():
    """زمینه Price Action صعودی"""
    return PriceActionContext(
        direction=DecisionDirection.BULLISH,
        direction_score=70,
        patterns=[
            {"name": "engulfing", "direction": "bullish", "score": 15},
            {"name": "pin_bar", "direction": "bullish", "score": 12}
        ],
        support_resistance={"support": 1.0840, "resistance": 1.0870},
        candle_strength=SignalStrength.STRONG
    )


@pytest.fixture
def bearish_pa_context():
    """زمینه Price Action نزولی"""
    return PriceActionContext(
        direction=DecisionDirection.BEARISH,
        direction_score=65,
        patterns=[
            {"name": "engulfing", "direction": "bearish", "score": 15}
        ],
        support_resistance={"support": 1.0840, "resistance": 1.0870},
        candle_strength=SignalStrength.MODERATE
    )


@pytest.fixture
def active_session_context():
    """زمینه سشن فعال"""
    return SessionContext(
        current_session=SessionType.LONDON,
        killzone_active=True,
        killzone_name="london",
        session_score=80,
        session_overlap=False
    )


@pytest.fixture
def active_license_context():
    """زمینه لایسنس معتبر"""
    return LicenseContext(
        is_valid=True,
        is_expired=False,
        license_type="pro",
        allowed_features=["auto_trade", "signals", "dashboard"],
        max_devices=3,
        devices_used=1
    )


@pytest.fixture
def valid_risk_context():
    """زمینه ریسک معتبر"""
    return RiskContext(
        daily_pnl=50.0,
        daily_trades=2,
        open_positions=1,
        max_daily_loss=-500.0,
        max_daily_trades=5,
        max_positions=3,
        risk_per_trade=0.02,
        available_margin=5000.0
    )


@pytest.fixture
def valid_symbol_policy():
    """سیاست نماد معتبر"""
    return SymbolPolicy(
        symbol="EURUSD",
        allowed=True,
        max_lot=1.0,
        min_lot=0.01,
        max_spread=5.0,
        max_slippage=3.0,
        allowed_sessions=["london", "new_york"]
    )


# =====================================================
# تست‌های BUY
# =====================================================

class TestBuyDecision:
    """تست‌های تصمیم خرید"""

    def test_buy_with_strong_signals(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست تصمیم BUY با سیگنال‌های قوی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.BUY
        assert result.direction == DecisionDirection.BULLISH
        assert result.allowed is True
        assert result.quality_score >= 60
        assert result.trading_levels is not None
        assert ReasonCode.SMC_BULLISH_BOS in result.reason_codes

    def test_buy_with_entry_levels(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست محاسبه سطوح ورود برای خرید"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy,
            volatility_context=VolatilityContext(atr=0.0020)
        )

        result = engine.make_decision(input_data)

        assert result.trading_levels is not None
        assert result.trading_levels.entry_zone == 1.0850
        assert result.trading_levels.stop_loss < result.trading_levels.entry_zone
        assert result.trading_levels.take_profit_1 > result.trading_levels.entry_zone
        assert result.trading_levels.risk_reward_ratio > 0

    def test_buy_with_mtf_alignment(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست خرید با همسویی چند تایم‌فریم"""
        mtf_context = MultiTimeframeContext(
            higher_timeframe_trend=MarketTrend.BULLISH,
            htf_alignment=True,
            htf_score=80,
            lower_timeframe_entry=True,
            ltf_score=70
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            mtf_context=mtf_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.BUY
        assert result.quality_score >= 70


# =====================================================
# تست‌های SELL
# =====================================================

class TestSellDecision:
    """تست‌های تصمیم فروش"""

    def test_sell_with_strong_signals(
        self,
        engine,
        bearish_smc_context,
        bearish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست تصمیم SELL با سیگنال‌های قوی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bearish_smc_context,
            price_action_context=bearish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.SELL
        assert result.direction == DecisionDirection.BEARISH
        assert result.allowed is True
        assert result.quality_score >= 55

    def test_sell_entry_levels(
        self,
        engine,
        bearish_smc_context,
        bearish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست محاسبه سطوح ورود برای فروش"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bearish_smc_context,
            price_action_context=bearish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy,
            volatility_context=VolatilityContext(atr=0.0020)
        )

        result = engine.make_decision(input_data)

        assert result.trading_levels is not None
        assert result.trading_levels.entry_zone == 1.0850
        assert result.trading_levels.stop_loss > result.trading_levels.entry_zone
        assert result.trading_levels.take_profit_1 < result.trading_levels.entry_zone


# =====================================================
# تست‌های NO_TRADE
# =====================================================

class TestNoTradeDecision:
    """تست‌های عدم معامله"""

    def test_no_trade_with_week_signals(self, engine, base_input):
        """تست NO_TRADE با سیگنال‌های ضعیف"""
        weak_smc = SMCContext(
            trend=MarketTrend.RANGING,
            trend_score=20,
            structure_event=None,
            structure_direction=None,
            structure_level=None,
            liquidity_swept=False,
            liquidity_direction=None,
            premium_discount="neutral"
        )

        weak_pa = PriceActionContext(
            direction=DecisionDirection.NEUTRAL,
            direction_score=10,
            patterns=[],
            candle_strength=SignalStrength.NONE
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=weak_smc,
            price_action_context=weak_pa,
            session_context=SessionContext(
                current_session=SessionType.CLOSED,
                killzone_active=False
            )
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert ReasonCode.INSUFFICIENT_SCORE in result.reason_codes

    def test_no_trade_outside_killzone(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست NO_TRADE خارج از Kill Zone"""
        inactive_session = SessionContext(
            current_session=SessionType.CLOSED,
            killzone_active=False,
            killzone_name=None,
            session_score=10
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=inactive_session,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert ReasonCode.OUTSIDE_KILLZONE in result.reason_codes

    def test_no_trade_no_direction(self, engine, base_input):
        """تست NO_TRADE بدون جهت مشخص"""
        neutral_smc = SMCContext(
            trend=MarketTrend.RANGING,
            trend_score=50,
            structure_event=None,
            structure_direction=None,
            structure_level=None,
            liquidity_swept=False,
            liquidity_direction=None,
            premium_discount="neutral"
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=neutral_smc
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert ReasonCode.NO_CLEAR_DIRECTION in result.reason_codes


# =====================================================
# تست‌های تعارض
# =====================================================

class TestConflictResolution:
    """تست‌های حل تعارض"""

    def test_conflict_smc_pa_opposite(
        self,
        engine,
        bullish_smc_context,
        bearish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست تعارض بین SMC صعودی و PA نزولی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bearish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        # در صورت تعارض باید یکی از این حالت‌ها باشد
        assert result.decision in [DecisionAction.NO_TRADE, DecisionAction.BUY]

    def test_conflict_resolution_smc_priority(
        self,
        engine,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست حل تعارض با اولویت SMC"""
        # SMC قوی صعودی
        strong_bullish_smc = SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=85,
            structure_event="BOS",
            structure_direction="bullish",
            structure_level=1.0860,
            liquidity_swept=True,
            liquidity_direction="bullish",
            premium_discount="discount"
        )

        # PA ضعیف نزولی
        weak_bearish_pa = PriceActionContext(
            direction=DecisionDirection.BEARISH,
            direction_score=30,
            patterns=[],
            candle_strength=SignalStrength.WEAK
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=strong_bullish_smc,
            price_action_context=weak_bearish_pa,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        # SMC باید اولویت داشته باشد
        assert result.decision == DecisionAction.BUY


# =====================================================
# تست‌های کیفیت پایین
# =====================================================

class TestLowQuality:
    """تست‌های کیفیت پایین"""

    def test_low_quality_no_trade(
        self,
        engine,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست NO_TRADE با کیفیت پایین"""
        low_score_smc = SMCContext(
            trend=MarketTrend.BULLISH,
            trend_score=25,
            structure_event=None,
            structure_direction=None,
            structure_level=None,
            liquidity_swept=False,
            liquidity_direction=None,
            premium_discount="neutral"
        )

        low_score_pa = PriceActionContext(
            direction=DecisionDirection.BULLISH,
            direction_score=20,
            patterns=[],
            candle_strength=SignalStrength.WEAK
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=low_score_smc,
            price_action_context=low_score_pa,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE or result.quality_score < 50


# =====================================================
# تست‌های بلاک لایسنس
# =====================================================

class TestLicenseBlocked:
    """تست‌های بلاک لایسنس"""

    def test_invalid_license_blocked(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست بلاک با لایسنس نامعتبر"""
        invalid_license = LicenseContext(
            is_valid=False,
            is_expired=False,
            license_type="trial",
            allowed_features=[],
            max_devices=1,
            devices_used=0
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=invalid_license,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.LICENSE_INVALID in result.blocked_reasons

    def test_expired_license_blocked(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست بلاک با لایسنس منقضی"""
        expired_license = LicenseContext(
            is_valid=True,
            is_expired=True,
            license_type="basic",
            allowed_features=[],
            max_devices=1,
            devices_used=1
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=expired_license,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.LICENSE_EXPIRED in result.blocked_reasons


# =====================================================
# تست‌های بلاک ریسک
# =====================================================

class TestRiskBlocked:
    """تست‌های بلاک ریسک"""

    def test_daily_loss_limit_blocked(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_symbol_policy
    ):
        """تست بلاک با رسیدن به حد ضرر روزانه"""
        exceeded_risk = RiskContext(
            daily_pnl=-600.0,
            daily_trades=3,
            open_positions=1,
            max_daily_loss=-500.0,
            max_daily_trades=5,
            max_positions=3,
            risk_per_trade=0.02,
            available_margin=1000.0
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=exceeded_risk,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.DAILY_LOSS_LIMIT in result.blocked_reasons

    def test_max_positions_blocked(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_symbol_policy
    ):
        """تست بلاک با حداکثر پوزیشن باز"""
        max_risk = RiskContext(
            daily_pnl=50.0,
            daily_trades=2,
            open_positions=3,
            max_daily_loss=-500.0,
            max_daily_trades=5,
            max_positions=3,
            risk_per_trade=0.02,
            available_margin=5000.0
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=max_risk,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.MAX_POSITIONS_REACHED in result.blocked_reasons

    def test_max_daily_trades_blocked(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_symbol_policy
    ):
        """تست بلاک با حداکثر معاملات روزانه"""
        max_trades_risk = RiskContext(
            daily_pnl=50.0,
            daily_trades=5,
            open_positions=1,
            max_daily_loss=-500.0,
            max_daily_trades=5,
            max_positions=3,
            risk_per_trade=0.02,
            available_margin=5000.0
        )

        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=max_trades_risk,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.MAX_TRADES_REACHED in result.blocked_reasons


# =====================================================
# تست‌های بلاک نماد
# =====================================================

class TestSymbolBlocked:
    """تست‌های بلاک نماد"""

    def test_symbol_not_allowed(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context
    ):
        """تست بلاک با نماد غیرمجاز"""
        blocked_symbol = SymbolPolicy(
            symbol="XAUUSD",
            allowed=False,
            max_lot=0.0,
            min_lot=0.0,
            max_spread=0.0,
            max_slippage=0.0,
            allowed_sessions=[],
            blocked_reason="نماد برای لایسنس Trial مجاز نیست"
        )

        input_data = DecisionInput(
            symbol="XAUUSD",
            timeframe="H1",
            current_price=1950.00,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=blocked_symbol
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.allowed is False
        assert BlockReason.SYMBOL_NOT_ALLOWED in result.blocked_reasons


# =====================================================
# تست‌های امتیازدهی
# =====================================================

class TestScoreCalculation:
    """تست‌های محاسبه امتیاز"""

    def test_score_breakdown(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست breakdown امتیازها"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        assert "smc" in result.score_breakdown
        assert "price_action" in result.score_breakdown
        assert "session" in result.score_breakdown
        assert result.quality_score > 0

    def test_total_score_calculation(self, engine):
        """تست محاسبه امتیاز کل"""
        scores = {
            "smc": 70,
            "price_action": 65,
            "mtf": 50,
            "session": 80,
            "liquidity": 40,
            "momentum": 30
        }

        total = engine._calculate_total_score(scores)

        assert 50 <= total <= 80


# =====================================================
# تست‌های Reason Codes
# =====================================================

class TestReasonCodes:
    """تست‌های کدهای دلیل"""

    def test_reason_codes_persian_translation(self, engine):
        """تست ترجمه کدهای دلیل به فارسی"""
        codes = [
            ReasonCode.SMC_BULLISH_BOS,
            ReasonCode.PA_BULLISH_ENGULFING,
            ReasonCode.KILLZONE_ACTIVE
        ]

        translations = engine._translate_reason_codes(codes)

        assert len(translations) == 3
        assert "BOS" in translations[0]
        assert "Engulfing" in translations[1]

    def test_block_reasons_persian(self, engine):
        """تست ترجمه دلایل بلاک"""
        reasons = [
            BlockReason.LICENSE_INVALID,
            BlockReason.DAILY_LOSS_LIMIT
        ]

        translations = engine._get_block_reasons_persian(reasons)

        assert "لایسنس" in translations[0]
        assert "ضرر" in translations[1]


# =====================================================
# تست‌های خروجی
# =====================================================

class TestOutputFormat:
    """تست‌های فرمت خروجی"""

    def test_output_structure(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست ساختار خروجی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        # بررسی فیلدهای الزامی
        assert result.symbol == "EURUSD"
        assert result.timeframe == "H1"
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.decision, DecisionAction)
        assert isinstance(result.direction, DecisionDirection)
        assert isinstance(result.confidence_score, int)
        assert isinstance(result.quality_score, int)
        assert isinstance(result.allowed, bool)
        assert isinstance(result.reason_codes, list)
        assert isinstance(result.reasons_persian, list)

    def test_trading_levels_structure(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست ساختار سطوح معاملاتی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        if result.decision == DecisionAction.BUY:
            assert result.trading_levels is not None
            assert result.trading_levels.entry_zone > 0
            assert result.trading_levels.stop_loss > 0
            assert result.trading_levels.take_profit_1 > 0
            assert result.trading_levels.risk_reward_ratio > 0

    def test_risk_profile_structure(
        self,
        engine,
        bullish_smc_context,
        bullish_pa_context,
        active_session_context,
        active_license_context,
        valid_risk_context,
        valid_symbol_policy
    ):
        """تست ساختار پروفایل ریسک"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            price_action_context=bullish_pa_context,
            session_context=active_session_context,
            license_context=active_license_context,
            risk_context=valid_risk_context,
            symbol_policy=valid_symbol_policy
        )

        result = engine.make_decision(input_data)

        if result.decision != DecisionAction.NO_TRADE:
            assert result.risk_profile is not None
            assert isinstance(result.risk_profile.risk_level, RiskLevel)
            assert result.risk_profile.position_size > 0


# =====================================================
# تست‌های Edge Cases
# =====================================================

class TestEdgeCases:
    """تست‌های موارد خاص"""

    def test_empty_input(self, engine):
        """تست با ورودی خالی"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850
        )

        result = engine.make_decision(input_data)

        assert result.decision == DecisionAction.NO_TRADE
        assert result.quality_score < 50

    def test_only_smc_context(
        self,
        engine,
        bullish_smc_context,
        active_session_context
    ):
        """تست با فقط زمینه SMC"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            smc_context=bullish_smc_context,
            session_context=active_session_context
        )

        result = engine.make_decision(input_data)

        # باید تصمیم‌گیری کند حتی بدون PA
        assert isinstance(result.decision, DecisionAction)

    def test_only_pa_context(
        self,
        engine,
        bullish_pa_context,
        active_session_context
    ):
        """تست با فقط زمینه PA"""
        input_data = DecisionInput(
            symbol="EURUSD",
            timeframe="H1",
            current_price=1.0850,
            price_action_context=bullish_pa_context,
            session_context=active_session_context
        )

        result = engine.make_decision(input_data)

        assert isinstance(result.decision, DecisionAction)


# =====================================================
# اجرای تست
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
