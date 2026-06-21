# مستندات سیستم معامله‌گری MT5

## فهرست مطالب

1. [معرفی سیستم](#معرفی-سیستم)
2. [معماری سیستم](#معماری-سیستم)
3. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
4. [پیکربندی](#پیکربندی)
5. [راهنمای استفاده](#راهنمای-استفاده)
6. [توسعه و تمدید](#توسعه-و-تمدید)

---

## معرفی سیستم

سیستم معامله‌گری MT5 یک پلتفرم جامع برای تحلیل و معامله‌گری خودکار در بازارهای مالی است. این سیستم از دو موتور تحلیلی اصلی تشکیل شده:

### موتور SMC (Smart Money Concept)
تحلیل ساختار بازار، نقدینگی، Order Blocks و FVG

### موتور Price Action
تشخیص الگوهای کندلی، ساختار قیمت و سطوح کلیدی

### موتور تصمیم‌گیری
ترکیب سیگنال‌ها و تولید تصمیم نهایی معاملاتی

---

## معماری سیستم

```
mt5-trading-system/
├── backend/                    # بک‌اند پایتون
│   ├── api/                     # FastAPI endpoints
│   │   ├── routes/             # مسیرهای API
│   │   ├── license_gate.py     # دروازه لایسنس
│   │   └── dependencies.py     # وابستگی‌ها
│   ├── analysis/               # موتورهای تحلیلی
│   │   ├── smc_engine.py       # موتور SMC
│   │   ├── price_action_engine.py
│   │   └── decision_engine.py  # موتور تصمیم‌گیری
│   ├── core/                   # هسته مرکزی
│   │   ├── config.py           # تنظیمات
│   │   ├── enums.py            # شمارش‌ها
│   │   └── exceptions.py       # استثناها
│   ├── database/               # دیتابیس
│   │   └── connection.py       # اتصال Supabase
│   ├── license/                # مدیریت لایسنس
│   │   └── manager.py          # مدیر لایسنس
│   ├── models/                 # مدل‌های داده
│   ├── services/               # سرویس‌ها
│   │   ├── license_service.py
│   │   ├── audit_service.py
│   │   └── rbac_service.py
│   ├── telegram/               # ربات تلگرام
│   │   ├── bot.py
│   │   ├── auth.py             # احراز هویت
│   │   ├── handlers/           # هندلرها
│   │   └── keyboards.py
│   ├── tests/                  # تست‌ها
│   └── contracts/              # قراردادها
├── frontend/                   # فرانت‌اند React
│   ├── src/
│   │   ├── pages/              # صفحات
│   │   ├── components/         # کامپوننت‌ها
│   │   ├── services/           # سرویس‌ها
│   │   └── contexts/           # Context ها
├── mql5/                       # Expert Advisor
│   ├── Experts/
│   │   └── MT5Trading/
│   │       └── MT5TradingEA.mq5
│   └── Include/
│       └── MT5Trading/
│           ├── DecisionConnector.mqh
│           └── LicenseManager.mqh
└── docs/                       # مستندات
```

---

## نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.11+
- Node.js 18+
- MetaTrader 5
- Supabase اکانت

### مراحل نصب Backend

1. کلون کردن پروژه:
```bash
git clone <repository-url>
cd mt5-trading-system/backend
```

2. ایجاد virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

4. کپی فایل .env:
```bash
cp .env.example .env
```

5. پیکربندی متغیرهای محیطی:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_DB_URL=your_database_url
JWT_SECRET_KEY=your_secret_key
TELEGRAM_BOT_TOKEN=your_bot_token
LICENSE_ENCRYPTION_KEY=your_32_byte_key
```

6. اجرای سرور:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### مراحل نصب Frontend

1. رفتن به پوشه frontend:
```bash
cd ../frontend
```

2. نصب وابستگی‌ها:
```bash
npm install
```

3. اجرای سرور توسعه:
```bash
npm run dev
```

### نصب EA در MT5

1. کپی پوشه `mql5` به `MQL5` در داده‌های MT5
2. کامپایل `MT5TradingEA.mq5`
3. فعال‌سازی "Allow automated trading"
4. اضافه کردن EA به چارت

---

## پیکربندی

### تنظیمات دیتابیس (Supabase)

#### جداول مورد نیاز

```sql
-- جدول کاربران
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE,
    telegram_username TEXT,
    email TEXT,
    role TEXT DEFAULT 'user',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول لایسنس‌ها
CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES user_profiles(id),
    license_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    max_devices INT DEFAULT 1,
    devices_used INT DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول دستگاه‌ها
CREATE TABLE license_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID REFERENCES licenses(id),
    device_id TEXT NOT NULL,
    device_name TEXT,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);

-- جدول اعتبارسنجی‌ها
CREATE TABLE license_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID,
    device_id TEXT,
    ip_address TEXT,
    is_valid BOOLEAN,
    status TEXT,
    blocked_reasons JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول سیگنال‌ها
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price DECIMAL(18,5),
    stop_loss DECIMAL(18,5),
    take_profit_1 DECIMAL(18,5),
    take_profit_2 DECIMAL(18,5),
    take_profit_3 DECIMAL(18,5),
    quality_score INT,
    confidence_score INT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- جدول معاملات
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id),
    user_id UUID REFERENCES user_profiles(id),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price DECIMAL(18,5),
    exit_price DECIMAL(18,5),
    volume DECIMAL(18,5),
    profit DECIMAL(18,5),
    status TEXT DEFAULT 'open',
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- جدول گزارش‌ها
CREATE TABLE trade_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    report_date DATE,
    total_trades INT,
    winning_trades INT,
    losing_trades INT,
    gross_profit DECIMAL(18,2),
    gross_loss DECIMAL(18,2),
    net_profit DECIMAL(18,2),
    win_rate DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول audit log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### RLS Policies

```sql
-- فعال‌سازی RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_reports ENABLE ROW LEVEL SECURITY;

-- Policy برای user_profiles
CREATE POLICY "users_read_own" ON user_profiles FOR SELECT
    TO authenticated USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON user_profiles FOR UPDATE
    TO authenticated USING (auth.uid() = id);

-- Policy برای signals
CREATE POLICY "signals_read_authenticated" ON signals FOR SELECT
    TO authenticated USING (true);

-- Policy برای trades
CREATE POLICY "trades_read_own" ON trades FOR SELECT
    TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "trades_insert_own" ON trades FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);
```

### تنظیمات ربات تلگرام

1. ایجاد ربات از طریق @BotFather
2. دریافت توکن
3. تنظیم در .env:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_IDS=[123456789, 987654321]
```

4. اجرای ربات:
```bash
python -m backend.telegram.bot
```

### تنظیمات لایسنس

انواع لایسنس:
- `trial`: 7 روز آزمایشی
- `basic`: 1 ماه پایه
- `pro`: 3 ماه حرفه‌ای
- `enterprise`: 1 سال سازمانی
- `lifetime`: مادام‌العمر

ویژگی‌های هر لایسنس:

| ویژگی | Trial | Basic | Pro | Enterprise | Lifetime |
|-------|-------|-------|-----|------------|----------|
| تحلیل SMC | ✓ | ✓ | ✓ | ✓ | ✓ |
| Price Action | ✓ | ✓ | ✓ | ✓ | ✓ |
| چند تایم‌فریم | ✗ | ✓ | ✓ | ✓ | ✓ |
| معامله دستی | ✗ | ✓ | ✓ | ✓ | ✓ |
| معامله خودکار | ✗ | ✗ | ✓ | ✓ | ✓ |
| ربات تلگرام | ✗ | ✓ | ✓ | ✓ | ✓ |
| داشبورد | ✗ | ✓ | ✓ | ✓ | ✓ |
| API Access | ✗ | ✗ | ✓ | ✓ | ✓ |
| استراتژی سفارشی | ✗ | ✗ | ✗ | ✓ | ✓ |

---

## راهنمای استفاده

### استفاده از داشبورد

1. ثبت‌نام در `/register`
2. ورود در `/login`
3. اتصال Telegram ID در تنظیمات
4. ثبت لایسنس

### استفاده از ربات تلگرام

دستورات اصلی:
- `/start` - شروع
- `/help` - راهنما
- `/status` - وضعیت اکانت
- `/balance` - موجودی
- `/trades` - لیست معاملات
- `/positions` - پوزیشن‌های باز
- `/signal` - آخرین سیگنال
- `/daily` - گزارش روزانه

### استفاده از EA

1. متصل کردن EA به API
2. تنظیم License Key
3. فعال‌سازی Auto Trading
4. تنظیم پارامترهای ریسک

---

## توسعه و تمدید

### اضافه کردن استراتژی جدید

1. ایجاد فایل در `backend/analysis/`
2. ارث‌بری از کلاس پایه
3. ثبت در Decision Engine
4. نوشتن تست‌ها

### اضافه کردن endpoint جدید

1. ایجاد فایل در `backend/api/routes/`
2. اضافه کردن authorization
3. ثبت در `main.py`
4. نوشتن تست‌های یکپارچه

### اضافه کردن دستور تلگرام

1. ایجاد handler در `backend/telegram/handlers/`
2. تعریف permission در `rbac.py`
3. ثبت در `bot.py`

---

## پشتیبانی

برای پشتیبانی و سوالات:
- تلگرام: @MT5Trading_Support
- ایمیل: support@mt5trading.com
