"""
موتور تصمیم‌گیری معاملاتی

این موتور سیگنال‌های SMC و Price Action را ترکیب کرده و تصمیم نهایی معاملاتی تولید می‌کند.

ویژگی‌ها:
- تصمیم‌گیری چندلایه
- حل تعارض سیگنال‌ها
- بررسی لایسنس و ریسک
- توضیح‌پذیری کامل با reason codes
- خروجی قابل استفاده برای MT5، API، Telegram و Dashboard

نویسنده: MT5 Trading Team
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging

from ..core.enums import (
    DecisionAction, DecisionDirection, DecisionQuality,
    DecisionConfidence, SignalStrength, MarketTrend,
    LiquidityState, SessionType, RiskLevel, ReasonCode, BlockReason
)

# تنظیم لاگر
logger = logging.getLogger("decision_engine")


# =====================================================
# ثابت‌های وزن‌دهی
# =====================================================
WEIGHTS = {
    "smc": 0.35,
    "price_action": 0.30,
    "mtf": 0.15,
    "session": 0.10,
    "liquidity": 0.05,
    "momentum": 0.05
}

# آستانه‌ها
SCORE_THRESHOLDS = {
    "excellent": 85,
    "good": 70,
    "moderate": 55,
    "low": 40,
    "min_trade": 45
}

CONFLICT_THRESHOLDS = {
    "max_divergence": 30,
    "min_agreement": 60
}


# =====================================================
# مدل‌های داده
# =====================================================

@dataclass
class SMCContext:
    """زمینه Smart Money Concept"""
    trend: MarketTrend
    trend_score: int
    structure_event: Optional[str]
    structure_direction: Optional[str]
    structure_level: Optional[float]
    liquidity_swept: bool
    liquidity_direction: Optional[str]
    premium_discount: str
    order_blocks: List[Dict[str, Any]] = field(default_factory=list)
    fvgs: List[Dict[str, Any]] = field(default_factory=list)
    swing_high: Optional[float] = None
    swing_low: Optional[float] = None


@dataclass
class PriceActionContext:
    """زمینه Price Action"""
    direction: DecisionDirection
    direction_score: int
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    support_resistance: Dict[str, Any] = field(default_factory=dict)
    candle_strength: SignalStrength = SignalStrength.NONE


@dataclass
class MultiTimeframeContext:
    """زمینه چند تایم‌فریم"""
    higher_timeframe_trend: MarketTrend = MarketTrend.RANGING
    htf_alignment: bool = False
    htf_score: int = 0
    lower_timeframe_entry: bool = False
    ltf_score: int = 0


@dataclass
class SessionContext:
    """زمینه سشن معاملاتی"""
    current_session: SessionType = SessionType.CLOSED
    killzone_active: bool = False
    killzone_name: Optional[str] = None
    session_score: int = 0
    session_overlap: bool = False


@dataclass
class LiquidityContext:
    """زمینه نقدینگی"""
    state: LiquidityState = LiquidityState.NONE
    buy_side_liquidity: List[float] = field(default_factory=list)
    sell_side_liquidity: List[float] = field(default_factory=list)
    sweep_score: int = 0


@dataclass
class VolatilityContext:
    """زمینه نوسان"""
    atr: float = 0.0
    atr_percentile: int = 0
    volatility_level: RiskLevel = RiskLevel.MEDIUM
    spread: float = 0.0
    spread_percentile: int = 0


@dataclass
class RiskContext:
    """زمینه ریسک"""
    daily_pnl: float = 0.0
    daily_trades: int = 0
    open_positions: int = 0
    max_daily_loss: float = -500.0
    max_daily_trades: int = 5
    max_positions: int = 3
    risk_per_trade: float = 0.02
    available_margin: float = 0.0


@dataclass
class LicenseContext:
    """زمینه لایسنس"""
    is_valid: bool = False
    is_expired: bool = False
    license_type: str = "trial"
    allowed_features: List[str] = field(default_factory=list)
    max_devices: int = 1
    devices_used: int = 0


@dataclass
class SymbolPolicy:
    """سیاست نماد"""
    symbol: str
    allowed: bool = True
    max_lot: float = 1.0
    min_lot: float = 0.01
    max_spread: float = 5.0
    max_slippage: float = 3.0
    allowed_sessions: List[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None


@dataclass
class DecisionInput:
    """
    ورودی تصمیم‌گیری

    شامل تمام داده‌های لازم برای تصمیم‌گیری معاملاتی
    """
    # نماد و تایم‌فریم
    symbol: str
    timeframe: str
    current_price: float

    # سیگنال‌های اصلی
    smc_context: Optional[SMCContext] = None
    price_action_context: Optional[PriceActionContext] = None

    # زمینه‌های تکمیلی
    mtf_context: Optional[MultiTimeframeContext] = None
    session_context: Optional[SessionContext] = None
    liquidity_context: Optional[LiquidityContext] = None
    volatility_context: Optional[VolatilityContext] = None

    # ریسک و لایسنس
    risk_context: Optional[RiskContext] = None
    license_context: Optional[LicenseContext] = None
    symbol_policy: Optional[SymbolPolicy] = None

    # تنظیمات کاربر
    user_settings: Dict[str, Any] = field(default_factory=dict)

    # timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TradingLevels:
    """سطوح معاملاتی"""
    entry_zone: float
    entry_zone_high: float
    entry_zone_low: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    invalidation_level: float
    risk_reward_ratio: float
    risk_percent: float


@dataclass
class RiskProfile:
    """پروفایل ریسک"""
    risk_level: RiskLevel
    position_size: float
    max_loss_amount: float
    potential_profit: float
    margin_required: float
    risk_reward_ratio: float


@dataclass
class DecisionOutput:
    """
    خروجی تصمیم‌گیری

    خروجی نهایی قابل استفاده برای MT5، API، Telegram و Dashboard
    """
    # اطلاعات پایه
    symbol: str
    timeframe: str
    created_at: datetime

    # تصمیم
    decision: DecisionAction
    direction: DecisionDirection
    confidence_score: int
    quality_score: int

    # معاملاتی
    trading_levels: Optional[TradingLevels] = None
    risk_profile: Optional[RiskProfile] = None

    # مجوز
    allowed: bool = True
    blocked_reasons: List[BlockReason] = field(default_factory=list)

    # توضیح
    reason_codes: List[ReasonCode] = field(default_factory=list)
    reasons_persian: List[str] = field(default_factory=list)

    # امتیازها
    score_breakdown: Dict[str, int] = field(default_factory=dict)
    component_scores: Dict[str, Any] = field(default_factory=dict)

    # متادیتا
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================
# موتور تصمیم‌گیری
# =====================================================

class DecisionEngine:
    """
    موتور تصمیم‌گیری معاملاتی

    سیگنال‌های SMC و Price Action را ترکیب کرده و تصمیم نهایی می‌گیرد.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        سازنده موتور تصمیم‌گیری

        Args:
            config: تنظیمات اختیاری
        """
        self.config = config or {}
        self.weights = self.config.get("weights", WEIGHTS)
        self.thresholds = self.config.get("thresholds", SCORE_THRESHOLDS)

        logger.info("موتور تصمیم‌گیری راه‌اندازی شد")

    def make_decision(self, input_data: DecisionInput) -> DecisionOutput:
        """
        تصمیم‌گیری نهایی

        Args:
            input_data: ورودی تصمیم‌گیری

        Returns:
            خروجی تصمیم‌گیری
        """
        logger.info(
            f"شروع تصمیم‌گیری برای {input_data.symbol} {input_data.timeframe}"
        )

        # مرحله 1: بررسی بلاک‌ها
        block_result = self._check_blocks(input_data)
        if block_result["blocked"]:
            return self._create_blocked_decision(input_data, block_result)

        # مرحله 2: محاسبه امتیازها
        scores = self._calculate_scores(input_data)

        # مرحله 3: تعیین جهت
        direction_result = self._determine_direction(input_data, scores)

        # مرحله 4: بررسی تعارض
        conflict_result = self._resolve_conflicts(input_data, direction_result)

        # مرحله 5: تصمیم نهایی
        final_decision = self._make_final_decision(
            input_data, scores, direction_result, conflict_result
        )

        # مرحله 6: محاسبه سطوح معاملاتی
        if final_decision.decision != DecisionAction.NO_TRADE:
            self._calculate_trading_levels(input_data, final_decision)
            self._calculate_risk_profile(input_data, final_decision)

        logger.info(
            f"تصمیم نهایی: {final_decision.decision.value} - "
            f"امتیاز: {final_decision.quality_score} - "
            f"جهت: {final_decision.direction.value}"
        )

        return final_decision

    def _check_blocks(self, input_data: DecisionInput) -> Dict[str, Any]:
        """
        بررسی بلاک‌های تصمیم‌گیری

        Returns:
            نتیجه بررسی بلاک
        """
        blocked_reasons: List[BlockReason] = []

        # بررسی لایسنس
        if input_data.license_context:
            if not input_data.license_context.is_valid:
                blocked_reasons.append(BlockReason.LICENSE_INVALID)
                logger.warning("لایسنس نامعتبر است")

            elif input_data.license_context.is_expired:
                blocked_reasons.append(BlockReason.LICENSE_EXPIRED)
                logger.warning("لایسنس منقضی شده است")

        # بررسی سیاست نماد
        if input_data.symbol_policy:
            if not input_data.symbol_policy.allowed:
                blocked_reasons.append(BlockReason.SYMBOL_NOT_ALLOWED)
                logger.warning(
                    f"نماد {input_data.symbol} مجاز نیست: "
                    f"{input_data.symbol_policy.blocked_reason}"
                )

        # بررسی ریسک
        if input_data.risk_context:
            risk_ctx = input_data.risk_context

            if risk_ctx.daily_pnl < risk_ctx.max_daily_loss:
                blocked_reasons.append(BlockReason.DAILY_LOSS_LIMIT)
                logger.warning("حد ضرر روزانه رسید")

            if risk_ctx.open_positions >= risk_ctx.max_positions:
                blocked_reasons.append(BlockReason.MAX_POSITIONS_REACHED)
                logger.warning("حداکثر پوزیشن‌های باز رسید")

            if risk_ctx.daily_trades >= risk_ctx.max_daily_trades:
                blocked_reasons.append(BlockReason.MAX_TRADES_REACHED)
                logger.warning("حداکثر معاملات روزانه رسید")

        return {
            "blocked": len(blocked_reasons) > 0,
            "reasons": blocked_reasons
        }

    def _create_blocked_decision(
        self,
        input_data: DecisionInput,
        block_result: Dict[str, Any]
    ) -> DecisionOutput:
        """
        ایجاد تصمیم بلاک شده

        Args:
            input_data: ورودی
            block_result: نتیجه بلاک

        Returns:
            تصمیم بلاک شده
        """
        reasons_persian = self._get_block_reasons_persian(block_result["reasons"])

        return DecisionOutput(
            symbol=input_data.symbol,
            timeframe=input_data.timeframe,
            created_at=datetime.utcnow(),
            decision=DecisionAction.NO_TRADE,
            direction=DecisionDirection.NEUTRAL,
            confidence_score=0,
            quality_score=0,
            allowed=False,
            blocked_reasons=block_result["reasons"],
            reason_codes=[ReasonCode.BLOCK_REASON_MAP.get(r, ReasonCode.LICENSE_BLOCKED)
                         for r in block_result["reasons"]],
            reasons_persian=reasons_persian,
            metadata={"block_type": "policy"}
        )

    def _calculate_scores(self, input_data: DecisionInput) -> Dict[str, int]:
        """
        محاسبه امتیازهای هر ماجول

        Args:
            input_data: ورودی

        Returns:
            دیکشنری امتیازها
        """
        scores = {
            "smc": 0,
            "price_action": 0,
            "mtf": 0,
            "session": 0,
            "liquidity": 0,
            "momentum": 0
        }

        # SMC Score
        if input_data.smc_context:
            scores["smc"] = self._calculate_smc_score(input_data.smc_context)

        # Price Action Score
        if input_data.price_action_context:
            scores["price_action"] = self._calculate_pa_score(
                input_data.price_action_context
            )

        # Multi-Timeframe Score
        if input_data.mtf_context:
            scores["mtf"] = self._calculate_mtf_score(input_data.mtf_context)

        # Session Score
        if input_data.session_context:
            scores["session"] = self._calculate_session_score(
                input_data.session_context
            )

        # Liquidity Score
        if input_data.liquidity_context:
            scores["liquidity"] = self._calculate_liquidity_score(
                input_data.liquidity_context
            )

        logger.debug(f"امتیازها: SMC={scores['smc']}, PA={scores['price_action']}, "
                    f"MTF={scores['mtf']}, Session={scores['session']}")

        return scores

    def _calculate_smc_score(self, smc_ctx: SMCContext) -> int:
        """
        محاسبه امتیاز SMC

        Args:
            smc_ctx: زمینه SMC

        Returns:
            امتیاز SMC
        """
        score = 0

        # امتیاز روند
        score += smc_ctx.trend_score * 30 // 100

        # امتیاز ساختار
        if smc_ctx.structure_event:
            event_scores = {
                "BOS": 25,
                "CHOCH": 20,
                "MSS": 15
            }
            score += event_scores.get(smc_ctx.structure_event, 0)

        # امتیاز نقدینگی
        if smc_ctx.liquidity_swept:
            score += 15

        # امتیاز Order Block
        if smc_ctx.order_blocks:
            active_blocks = [b for b in smc_ctx.order_blocks if b.get("active", True)]
            score += min(len(active_blocks) * 5, 15)

        # امتیاز FVG
        if smc_ctx.fvgs:
            active_fvgs = [f for f in smc_ctx.fvgs if f.get("fill_percent", 100) < 80]
            score += min(len(active_fvgs) * 5, 10)

        return min(score, 100)

    def _calculate_pa_score(self, pa_ctx: PriceActionContext) -> int:
        """
        محاسبه امتیاز Price Action

        Args:
            pa_ctx: زمینه Price Action

        Returns:
            امتیاز Price Action
        """
        score = 0

        # امتیاز جهت
        score += pa_ctx.direction_score * 40 // 100

        # امتیاز الگوها
        pattern_scores = {
            "engulfing": 15,
            "pin_bar": 12,
            "fakey": 18,
            "inside_bar": 8,
            "outside_bar": 10,
            "doji": 5
        }

        for pattern in pa_ctx.patterns[:3]:
            pattern_name = pattern.get("name", "").lower()
            pattern_score = pattern_scores.get(pattern_name, 5)
            direction_bonus = 1.2 if pattern.get("direction") == pa_ctx.direction.value else 1.0
            score += int(pattern_score * direction_bonus)

        # امتیاز قدرت کندل
        strength_scores = {
            SignalStrength.STRONG: 15,
            SignalStrength.MODERATE: 10,
            SignalStrength.WEAK: 5,
            SignalStrength.NONE: 0
        }
        score += strength_scores.get(pa_ctx.candle_strength, 0)

        return min(score, 100)

    def _calculate_mtf_score(self, mtf_ctx: MultiTimeframeContext) -> int:
        """
        محاسبه امتیاز چند تایم‌فریم

        Args:
            mtf_ctx: زمینه MTF

        Returns:
            امتیاز MTF
        """
        score = 0

        if mtf_ctx.htf_alignment:
            score += 50

        score += mtf_ctx.htf_score * 30 // 100

        if mtf_ctx.lower_timeframe_entry:
            score += 20

        return min(score, 100)

    def _calculate_session_score(self, session_ctx: SessionContext) -> int:
        """
        محاسبه امتیاز سشن

        Args:
            session_ctx: زمینه سشن

        Returns:
            امتیاز سشن
        """
        score = 0

        if session_ctx.killzone_active:
            score += 40

        if session_ctx.session_overlap:
            score += 30

        session_scores = {
            SessionType.LONDON: 20,
            SessionType.NEW_YORK: 20,
            SessionType.OVERLAP: 30,
            SessionType.ASIAN: 10,
            SessionType.CLOSED: 0
        }
        score += session_scores.get(session_ctx.current_session, 0)

        return min(score, 100)

    def _calculate_liquidity_score(self, liq_ctx: LiquidityContext) -> int:
        """
        محاسبه امتیاز نقدینگی

        Args:
            liq_ctx: زمینه نقدینگی

        Returns:
            امتیاز نقدینگی
        """
        score = 0

        state_scores = {
            LiquidityState.SWEPT: 40,
            LiquidityState.AVAILABLE: 30,
            LiquidityState.PARTIAL: 20,
            LiquidityState.NONE: 0
        }
        score += state_scores.get(liq_ctx.state, 0)

        score += liq_ctx.sweep_score * 60 // 100

        return min(score, 100)

    def _determine_direction(
        self,
        input_data: DecisionInput,
        scores: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        تعیین جهت معامله

        Args:
            input_data: ورودی
            scores: امتیازها

        Returns:
            نتیجه تعیین جهت
        """
        bullish_score = 0
        bearish_score = 0
        reasons: List[ReasonCode] = []

        # SMC Direction
        if input_data.smc_context:
            smc = input_data.smc_context
            if smc.trend == MarketTrend.BULLISH:
                bullish_score += scores["smc"] * 50 // 100
                if smc.structure_event in ["BOS", "CHOCH", "MSS"]:
                    if smc.structure_direction == "bullish":
                        reasons.append(ReasonCode.SMC_BULLISH_BOS)
                        bullish_score += 20
            elif smc.trend == MarketTrend.BEARISH:
                bearish_score += scores["smc"] * 50 // 100
                if smc.structure_event in ["BOS", "CHOCH", "MSS"]:
                    if smc.structure_direction == "bearish":
                        reasons.append(ReasonCode.SMC_BEARISH_BOS)
                        bearish_score += 20

            if smc.liquidity_swept and smc.liquidity_direction:
                if smc.liquidity_direction == "bullish":
                    reasons.append(ReasonCode.SMC_LIQUIDITY_SWEEP_BULLISH)
                    bullish_score += 15
                elif smc.liquidity_direction == "bearish":
                    reasons.append(ReasonCode.SMC_LIQUIDITY_SWEEP_BEARISH)
                    bearish_score += 15

        # Price Action Direction
        if input_data.price_action_context:
            pa = input_data.price_action_context

            for pattern in pa.patterns[:3]:
                name = pattern.get("name", "").lower()
                direction = pattern.get("direction", "")

                if direction == "bullish":
                    if name == "engulfing":
                        reasons.append(ReasonCode.PA_BULLISH_ENGULFING)
                    elif name == "pin_bar":
                        reasons.append(ReasonCode.PA_BULLISH_PIN_BAR)
                    bullish_score += 10
                elif direction == "bearish":
                    if name == "engulfing":
                        reasons.append(ReasonCode.PA_BEARISH_ENGULFING)
                    elif name == "pin_bar":
                        reasons.append(ReasonCode.PA_BEARISH_PIN_BAR)
                    bearish_score += 10

        # تعیین جهت نهایی
        total = bullish_score + bearish_score
        if total == 0:
            direction = DecisionDirection.NEUTRAL
            confidence = 0
        else:
            if bullish_score > bearish_score:
                direction = DecisionDirection.BULLISH
                confidence = int(bullish_score * 100 / (total + 1))
            elif bearish_score > bullish_score:
                direction = DecisionDirection.BEARISH
                confidence = int(bearish_score * 100 / (total + 1))
            else:
                direction = DecisionDirection.NEUTRAL
                confidence = 50

        return {
            "direction": direction,
            "confidence": confidence,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "reasons": reasons
        }

    def _resolve_conflicts(
        self,
        input_data: DecisionInput,
        direction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        حل تعارض بین سیگنال‌ها

        Args:
            input_data: ورودی
            direction_result: نتیجه تعیین جهت

        Returns:
            نتیجه حل تعارض
        """
        is_conflict = False
        conflict_reasons: List[str] = []
        resolution = "none"

        smc_dir = None
        pa_dir = None

        if input_data.smc_context:
            smc_dir = input_data.smc_context.trend.value

        if input_data.price_action_context:
            pa_dir = input_data.price_action_context.direction.value

        # بررسی تعارض
        if smc_dir and pa_dir:
            if smc_dir != "ranging" and pa_dir != "neutral":
                if smc_dir != pa_dir:
                    # تعارض بین SMC و PA
                    divergence = abs(
                        direction_result["bullish_score"] -
                        direction_result["bearish_score"]
                    )

                    if divergence < CONFLICT_THRESHOLDS["max_divergence"]:
                        is_conflict = True
                        conflict_reasons.append(
                            f"تعارض بین SMC ({smc_dir}) و Price Action ({pa_dir})"
                        )

                        # حل تعارض - SMC اولویت دارد
                        if input_data.smc_context.trend_score >= 70:
                            resolution = "smc_priority"
                            logger.info(
                                "تعارض با اولویت SMC حل شد: "
                                f"SMC={smc_dir}, PA={pa_dir}"
                            )
                        else:
                            resolution = "no_trade"
                            conflict_reasons.append("کیفیت سیگنال برای حل تعارض کافی نیست")

        return {
            "is_conflict": is_conflict,
            "conflict_reasons": conflict_reasons,
            "resolution": resolution
        }

    def _make_final_decision(
        self,
        input_data: DecisionInput,
        scores: Dict[str, int],
        direction_result: Dict[str, Any],
        conflict_result: Dict[str, Any]
    ) -> DecisionOutput:
        """
        تصمیم‌گیری نهایی

        Args:
            input_data: ورودی
            scores: امتیازها
            direction_result: نتیجه جهت
            conflict_result: نتیجه تعارض

        Returns:
            خروجی تصمیم‌گیری
        """
        # محاسبه امتیاز کل
        total_score = self._calculate_total_score(scores)

        # جمع‌آوری دلایل
        reason_codes: List[ReasonCode] = []
        reasons_persian: List[str] = []

        # بررسی تعارض
        if conflict_result["resolution"] == "no_trade":
            reason_codes.append(ReasonCode.CONFLICT_SIGNALS)
            reasons_persian.extend(conflict_result["conflict_reasons"])

            return DecisionOutput(
                symbol=input_data.symbol,
                timeframe=input_data.timeframe,
                created_at=datetime.utcnow(),
                decision=DecisionAction.NO_TRADE,
                direction=DecisionDirection.NEUTRAL,
                confidence_score=0,
                quality_score=total_score,
                allowed=True,
                reason_codes=reason_codes,
                reasons_persian=reasons_persian,
                score_breakdown=scores,
                metadata={"conflict": True}
            )

        # بررسی امتیاز حداقل
        if total_score < self.thresholds["min_trade"]:
            reason_codes.append(ReasonCode.INSUFFICIENT_SCORE)
            reasons_persian.append(
                f"امتیاز کل ({total_score}) کمتر از حداقل مجاز "
                f"({self.thresholds['min_trade']}) است"
            )

            return DecisionOutput(
                symbol=input_data.symbol,
                timeframe=input_data.timeframe,
                created_at=datetime.utcnow(),
                decision=DecisionAction.NO_TRADE,
                direction=direction_result["direction"],
                confidence_score=direction_result["confidence"],
                quality_score=total_score,
                allowed=True,
                reason_codes=reason_codes,
                reasons_persian=reasons_persian,
                score_breakdown=scores,
                metadata={"low_score": True}
            )

        # بررسی سشن
        if input_data.session_context:
            if not input_data.session_context.killzone_active:
                reason_codes.append(ReasonCode.OUTSIDE_KILLZONE)
                reasons_persian.append("خارج از Kill Zone")

                return DecisionOutput(
                    symbol=input_data.symbol,
                    timeframe=input_data.timeframe,
                    created_at=datetime.utcnow(),
                    decision=DecisionAction.NO_TRADE,
                    direction=direction_result["direction"],
                    confidence_score=direction_result["confidence"],
                    quality_score=total_score,
                    allowed=True,
                    reason_codes=reason_codes,
                    reasons_persian=reasons_persian,
                    score_breakdown=scores,
                    metadata={"outside_killzone": True}
                )

        # تصمیم نهایی
        if direction_result["direction"] == DecisionDirection.NEUTRAL:
            decision = DecisionAction.NO_TRADE
            reason_codes.append(ReasonCode.NO_CLEAR_DIRECTION)
            reasons_persian.append("جهت مشخصی شناسایی نشد")
        elif direction_result["direction"] == DecisionDirection.BULLISH:
            decision = DecisionAction.BUY
            reason_codes.extend(direction_result["reasons"])
        else:
            decision = DecisionAction.SELL
            reason_codes.extend(direction_result["reasons"])

        # تبدیل reason codes به فارسی
        reasons_persian.extend(self._translate_reason_codes(reason_codes))

        # تعیین کیفیت
        quality = self._determine_quality(total_score)

        # تعیین اعتماد
        confidence = self._determine_confidence(direction_result["confidence"])

        return DecisionOutput(
            symbol=input_data.symbol,
            timeframe=input_data.timeframe,
            created_at=datetime.utcnow(),
            decision=decision,
            direction=direction_result["direction"],
            confidence_score=direction_result["confidence"],
            quality_score=total_score,
            allowed=True,
            reason_codes=reason_codes,
            reasons_persian=reasons_persian,
            score_breakdown=scores,
            metadata={
                "quality": quality.value,
                "confidence": confidence.value
            }
        )

    def _calculate_total_score(self, scores: Dict[str, int]) -> int:
        """
        محاسبه امتیاز کل با وزن

        Args:
            scores: امتیازهای اجزا

        Returns:
            امتیاز کل
        """
        total = 0
        total_weight = 0

        for component, score in scores.items():
            weight = self.weights.get(component, 0)
            total += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        return int(total * 100 / total_weight)

    def _determine_quality(self, score: int) -> DecisionQuality:
        """
        تعیین کیفیت تصمیم

        Args:
            score: امتیاز

        Returns:
            کیفیت تصمیم
        """
        if score >= self.thresholds["excellent"]:
            return DecisionQuality.EXCELLENT
        elif score >= self.thresholds["good"]:
            return DecisionQuality.GOOD
        elif score >= self.thresholds["moderate"]:
            return DecisionQuality.MODERATE
        elif score >= self.thresholds["low"]:
            return DecisionQuality.LOW
        return DecisionQuality.POOR

    def _determine_confidence(self, confidence: int) -> DecisionConfidence:
        """
        تعیین سطح اعتماد

        Args:
            confidence: درصد اعتماد

        Returns:
            سطح اعتماد
        """
        if confidence >= 75:
            return DecisionConfidence.HIGH
        elif confidence >= 50:
            return DecisionConfidence.MEDIUM
        return DecisionConfidence.LOW

    def _calculate_trading_levels(
        self,
        input_data: DecisionInput,
        output: DecisionOutput
    ) -> None:
        """
        محاسبه سطوح معاملاتی

        Args:
            input_data: ورودی
            output: خروجی برای آپدیت
        """
        price = input_data.current_price

        # محاسبه buffer بر اساس ATR
        buffer = 0.0010  # پیش‌فرض
        if input_data.volatility_context:
            buffer = input_data.volatility_context.atr * 0.5

        # تعیین جهت
        is_buy = output.decision == DecisionAction.BUY

        # محاسبه سطوح
        if is_buy:
            entry = price
            sl = price - buffer * 2.5
            tp1 = price + buffer * 2.0
            tp2 = price + buffer * 4.0
            tp3 = price + buffer * 6.0
            invalidation = price - buffer * 4.0
            entry_low = price - buffer * 0.3
            entry_high = price + buffer * 0.3
        else:
            entry = price
            sl = price + buffer * 2.5
            tp1 = price - buffer * 2.0
            tp2 = price - buffer * 4.0
            tp3 = price - buffer * 6.0
            invalidation = price + buffer * 4.0
            entry_low = price - buffer * 0.3
            entry_high = price + buffer * 0.3

        # محاسبه R:R
        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        rr = reward / risk if risk > 0 else 0

        output.trading_levels = TradingLevels(
            entry_zone=entry,
            entry_zone_high=entry_high,
            entry_zone_low=entry_low,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            invalidation_level=invalidation,
            risk_reward_ratio=round(rr, 2),
            risk_percent=2.0
        )

        logger.debug(
            f"سطوح: Entry={entry:.5f}, SL={sl:.5f}, TP1={tp1:.5f}, R:R={rr:.2f}"
        )

    def _calculate_risk_profile(
        self,
        input_data: DecisionInput,
        output: DecisionOutput
    ) -> None:
        """
        محاسبه پروفایل ریسک

        Args:
            input_data: ورودی
            output: خروجی برای آپدیت
        """
        position_size = 0.01
        max_loss = 50.0
        potential_profit = 100.0
        margin = 100.0

        if input_data.risk_context:
            risk_ctx = input_data.risk_context
            max_loss = abs(risk_ctx.max_daily_loss) * risk_ctx.risk_per_trade

        if output.trading_levels:
            potential_profit = max_loss * output.trading_levels.risk_reward_ratio

        # تعیین سطح ریسک
        if output.quality_score >= 70:
            risk_level = RiskLevel.MEDIUM
        elif output.quality_score >= 55:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME

        output.risk_profile = RiskProfile(
            risk_level=risk_level,
            position_size=position_size,
            max_loss_amount=max_loss,
            potential_profit=potential_profit,
            margin_required=margin,
            risk_reward_ratio=output.trading_levels.risk_reward_ratio
            if output.trading_levels else 0
        )

    def _translate_reason_codes(self, codes: List[ReasonCode]) -> List[str]:
        """
        ترجمه کدهای دلیل به فارسی

        Args:
            codes: کدهای دلیل

        Returns:
            لیست متن‌های فارسی
        """
        translations = {
            ReasonCode.SMC_BULLISH_BOS: "BOS صعودی تشکیل شد",
            ReasonCode.SMC_BULLISH_CHOCH: "CHOCH صعودی تشکیل شد",
            ReasonCode.SMC_BULLISH_MSS: "MSS صعودی تشکیل شد",
            ReasonCode.SMC_BULLISH_OB: "Order Block صعودی فعال شد",
            ReasonCode.SMC_BULLISH_FVG: "FVG صعودی در حال پر شدن",
            ReasonCode.SMC_LIQUIDITY_SWEEP_BULLISH: "اسویپ نقدینگی صعودی",
            ReasonCode.SMC_BEARISH_BOS: "BOS نزولی تشکیل شد",
            ReasonCode.SMC_BEARISH_CHOCH: "CHOCH نزولی تشکیل شد",
            ReasonCode.SMC_BEARISH_MSS: "MSS نزولی تشکیل شد",
            ReasonCode.SMC_BEARISH_OB: "Order Block نزولی فعال شد",
            ReasonCode.SMC_BEARISH_FVG: "FVG نزولی در حال پر شدن",
            ReasonCode.SMC_LIQUIDITY_SWEEP_BEARISH: "اسویپ نقدینگی نزولی",
            ReasonCode.PA_BULLISH_ENGULFING: "الگوی Engulfing صعودی",
            ReasonCode.PA_BULLISH_PIN_BAR: "الگوی Pin Bar صعودی",
            ReasonCode.PA_BULLISH_FAKEY: "الگوی Fakey صعودی",
            ReasonCode.PA_SUPPORT_HOLD: "سطوح حمایتی حفظ شد",
            ReasonCode.PA_BEARISH_ENGULFING: "الگوی Engulfing نزولی",
            ReasonCode.PA_BEARISH_PIN_BAR: "الگوی Pin Bar نزولی",
            ReasonCode.PA_BEARISH_FAKEY: "الگوی Fakey نزولی",
            ReasonCode.PA_RESISTANCE_HOLD: "سطوح مقاومتی حفظ شد",
            ReasonCode.KILLZONE_ACTIVE: "Kill Zone فعال است",
            ReasonCode.MTF_ALIGNMENT: "همسویی چند تایم‌فریم",
            ReasonCode.SESSION_ALIGNMENT: "همسویی سشن معاملاتی"
        }

        return [translations.get(code, code.value) for code in codes]

    def _get_block_reasons_persian(self, reasons: List[BlockReason]) -> List[str]:
        """
        ترجمه دلایل بلاک به فارسی

        Args:
            reasons: دلایل بلاک

        Returns:
            لیست متن‌های فارسی
        """
        translations = {
            BlockReason.NONE: "",
            BlockReason.LICENSE_INVALID: "لایسنس نامعتبر است",
            BlockReason.LICENSE_EXPIRED: "لایسنس منقضی شده است",
            BlockReason.LICENSE_FEATURE_NOT_ALLOWED: "این ویژگی در لایسنس شما موجود نیست",
            BlockReason.SYMBOL_NOT_ALLOWED: "معامله این نماد مجاز نیست",
            BlockReason.RISK_EXCEEDED: "ریسک از حد مجاز فراتر رفته است",
            BlockReason.DAILY_LOSS_LIMIT: "حد ضرر روزانه رسید",
            BlockReason.MAX_POSITIONS_REACHED: "حداکثر پوزیشن‌های باز رسید",
            BlockReason.MAX_TRADES_REACHED: "حداکثر معاملات روزانه رسید",
            BlockReason.COOLDOWN_PERIOD: "دوره cooldown فعال است",
            BlockReason.INSUFFICIENT_MARGIN: "مارجین کافی نیست"
        }

        return [translations.get(r, r.value) for r in reasons if r != BlockReason.NONE]


# Map block reasons to reason codes
ReasonCode.BLOCK_REASON_MAP = {
    BlockReason.LICENSE_INVALID: ReasonCode.LICENSE_BLOCKED,
    BlockReason.LICENSE_EXPIRED: ReasonCode.LICENSE_BLOCKED,
    BlockReason.LICENSE_FEATURE_NOT_ALLOWED: ReasonCode.LICENSE_BLOCKED,
    BlockReason.SYMBOL_NOT_ALLOWED: ReasonCode.SYMBOL_BLOCKED,
    BlockReason.RISK_EXCEEDED: ReasonCode.RISK_BLOCKED,
    BlockReason.DAILY_LOSS_LIMIT: ReasonCode.RISK_BLOCKED,
    BlockReason.MAX_POSITIONS_REACHED: ReasonCode.MAX_TRADES_REACHED,
    BlockReason.MAX_TRADES_REACHED: ReasonCode.MAX_TRADES_REACHED,
    BlockReason.COOLDOWN_PERIOD: ReasonCode.COOLDOWN_ACTIVE
}
