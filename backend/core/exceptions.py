"""
استثناهای سیستم

نویسنده: MT5 Trading Team
"""


class MT5TradingError(Exception):
    """خطای پایه سیستم MT5 Trading"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AnalysisError(MT5TradingError):
    """خطای تحلیل"""

    def __init__(self, message: str, analysis_type: str = "unknown"):
        super().__init__(message, f"ANALYSIS_ERROR_{analysis_type.upper()}")
        self.analysis_type = analysis_type


class DecisionError(MT5TradingError):
    """خطای تصمیم‌گیری"""

    def __init__(self, message: str, decision_stage: str = "unknown"):
        super().__init__(message, f"DECISION_ERROR_{decision_stage.upper()}")
        self.decision_stage = decision_stage


class LicenseError(MT5TradingError):
    """خطای لایسنس"""

    def __init__(self, message: str, license_type: str = "unknown"):
        super().__init__(message, "LICENSE_ERROR")
        self.license_type = license_type


class RiskError(MT5TradingError):
    """خطای ریسک"""

    def __init__(self, message: str, risk_type: str = "unknown"):
        super().__init__(message, f"RISK_ERROR_{risk_type.upper()}")
        self.risk_type = risk_type


class DataError(MT5TradingError):
    """خطای داده"""

    def __init__(self, message: str, data_type: str = "unknown"):
        super().__init__(message, f"DATA_ERROR_{data_type.upper()}")
        self.data_type = data_type


class ValidationError(MT5TradingError):
    """خطای اعتبارسنجی"""

    def __init__(self, message: str, field: str = "unknown"):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
