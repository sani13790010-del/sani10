"""
انواع شماراییسیستم معاملاتی

نویسنده: MT5 Trading Team
"""

from enum import Enum


class DecisionAction(Enum):
    """عمل تصمیم‌گیری"""
    NO_TRADE = "NO_TRADE"
    BUY = "BUY"
    SELL = "SELL"


class DecisionDirection(Enum):
    """جهت تصمیم"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class DecisionQuality(Enum):
    """کیفیت تصمیم"""
    EXCELLENT = "excellent"      # >= 85
    GOOD = "good"                # >= 70
    MODERATE = "moderate"        # >= 55
    LOW = "low"                  # >= 40
    POOR = "poor"                # < 40


class DecisionConfidence(Enum):
    """اعتماد تصمیم"""
    HIGH = "high"          # >= 75
    MEDIUM = "medium"      # >= 50
    LOW = "low"            # < 50


class SignalStrength(Enum):
    """قدرت سیگنال"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


class MarketTrend(Enum):
    """روند بازار"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"
    TRANSITIONAL = "transitional"


class LiquidityState(Enum):
    """وضعیت نقدینگی"""
    SWEPT = "swept"
    AVAILABLE = "available"
    PARTIAL = "partial"
    NONE = "none"


class SessionType(Enum):
    """نوع سشن"""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP = "overlap"
    CLOSED = "closed"


class RiskLevel(Enum):
    """سطح ریسک"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ReasonCode(Enum):
    """کدهای دلیل تصمیم"""
    # مثبت - خرید
    SMC_BULLISH_BOS = "SMC_BULLISH_BOS"
    SMC_BULLISH_CHOCH = "SMC_BULLISH_CHOCH"
    SMC_BULLISH_MSS = "SMC_BULLISH_MSS"
    SMC_BULLISH_OB = "SMC_BULLISH_OB"
    SMC_BULLISH_FVG = "SMC_BULLISH_FVG"
    SMC_LIQUIDITY_SWEEP_BULLISH = "SMC_LIQUIDITY_SWEEP_BULLISH"
    PA_BULLISH_ENGULFING = "PA_BULLISH_ENGULFING"
    PA_BULLISH_PIN_BAR = "PA_BULLISH_PIN_BAR"
    PA_BULLISH_FAKEY = "PA_BULLISH_FAKEY"
    PA_BULLISH_INSIDE_BAR = "PA_BULLISH_INSIDE_BAR"
    PA_SUPPORT_HOLD = "PA_SUPPORT_HOLD"

    # مثبت - فروش
    SMC_BEARISH_BOS = "SMC_BEARISH_BOS"
    SMC_BEARISH_CHOCH = "SMC_BEARISH_CHOCH"
    SMC_BEARISH_MSS = "SMC_BEARISH_MSS"
    SMC_BEARISH_OB = "SMC_BEARISH_OB"
    SMC_BEARISH_FVG = "SMC_BEARISH_FVG"
    SMC_LIQUIDITY_SWEEP_BEARISH = "SMC_LIQUIDITY_SWEEP_BEARISH"
    PA_BEARISH_ENGULFING = "PA_BEARISH_ENGULFING"
    PA_BEARISH_PIN_BAR = "PA_BEARISH_PIN_BAR"
    PA_BEARISH_FAKEY = "PA_BEARISH_FAKEY"
    PA_BEARISH_INSIDE_BAR = "PA_BEARISH_INSIDE_BAR"
    PA_RESISTANCE_HOLD = "PA_RESISTANCE_HOLD"

    # سشن
    KILLZONE_ACTIVE = "KILLZONE_ACTIVE"
    SESSION_ALIGNMENT = "SESSION_ALIGNMENT"
    MTF_ALIGNMENT = "MTF_ALIGNMENT"

    # منفی - عدم معامله
    CONFLICT_SIGNALS = "CONFLICT_SIGNALS"
    LOW_QUALITY = "LOW_QUALITY"
    INSUFFICIENT_SCORE = "INSUFFICIENT_SCORE"
    NO_CLEAR_DIRECTION = "NO_CLEAR_DIRECTION"
    OUTSIDE_KILLZONE = "OUTSIDE_KILLZONE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"

    # بلاک
    LICENSE_BLOCKED = "LICENSE_BLOCKED"
    SYMBOL_BLOCKED = "SYMBOL_BLOCKED"
    RISK_BLOCKED = "RISK_BLOCKED"
    MAX_TRADES_REACHED = "MAX_TRADES_REACHED"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"


class BlockReason(Enum):
    """دلیل بلاک"""
    NONE = "none"
    LICENSE_INVALID = "license_invalid"
    LICENSE_EXPIRED = "license_expired"
    LICENSE_FEATURE_NOT_ALLOWED = "license_feature_not_allowed"
    SYMBOL_NOT_ALLOWED = "symbol_not_allowed"
    RISK_EXCEEDED = "risk_exceeded"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MAX_POSITIONS_REACHED = "max_positions_reached"
    COOLDOWN_PERIOD = "cooldown_period"
    INSUFFICIENT_MARGIN = "insufficient_margin"
