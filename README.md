# VIX/SPX Trading Signal Bot

A Python-based trading signal system that monitors VIX term structure and SPX trend conditions to identify high-probability entry points.

> **📖 [Full Strategy Documentation](STRATEGY_DOCUMENTATION.md)** - Comprehensive guide covering theory, decile analysis, backtested performance, and risk management.

## Strategy Overview

The system generates BUY signals based on VIX term structure inversion (backwardation) combined with SPX trend filters:

| Condition | Description |
|-----------|-------------|
| **Backwardation** | VIX/VIX3M Ratio > 1.0 (short-term fear elevated) |
| **MA Smoother** | 5-day SMA of VIX/VIX3M Ratio > 1.0 |
| **Trend Filter** | SPX position relative to moving averages |

### Best Performing Scenarios (Backtested)

| Scenario | Avg Return | Avg MDD | Win Rate | Return/MDD |
|----------|------------|---------|----------|------------|
| Backwardation + SPX > EMA_20 | 16.71% | -16.48% | 68.5% | 1.014 |
| Backwardation + SPX > SMA_20 | 15.70% | -18.59% | 66.2% | 0.844 |
| Backwardation + SPX < SMA_200 | 18.40% | -22.10% | 76.5% | 0.833 |

## Files

| File | Description |
|------|-------------|
| `STRATEGY_DOCUMENTATION.md` | **Master documentation** - full strategy guide with decile analysis |
| `daily_signal_tracker.py` | Main bot - fetches live data and sends Telegram alerts |
| `trend_filter_matrix_evaluation.py` | Backtesting framework for strategy optimization |
| `backtest_analysis.py` | Historical performance analysis |
| `signal_evaluation.py` | Signal quality evaluation |
| `distribution_analysis.py` | Return distribution analysis |
| `trend_filter_analysis.py` | Trend filter comparison |

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Telegram Bot

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Get your Chat ID via [@userinfobot](https://t.me/userinfobot)
3. Set environment variables:

**Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token_here
export TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Run the Bot

```bash
python daily_signal_tracker.py
```

## Sample Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DAILY SIGNAL EXECUTION TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Date: 2026-03-03

 MARKET LEVELS
   SPX:    5,234.18
   VIX:    22.45
   VIX3M:  20.12

 KEY INDICATORS
   VIX/VIX3M Ratio:     1.1158
   Ratio 5d SMA:        1.0842
   SPX 200d SMA:        5,180.25
   SPX 200d EMA:        5,195.40

 SIGNAL CONDITIONS
   Ratio 5d SMA > 1.0:  YES
   SPX < 200d SMA:      NO
   SPX < 200d EMA:      NO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 VERDICT: NO-GO (WAIT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Scheduling (Optional)

To run daily at market close, use:

**Windows Task Scheduler** or **cron** (Linux/Mac):

```bash
# Run at 4:30 PM ET every weekday
30 16 * * 1-5 cd /path/to/repo && python daily_signal_tracker.py
```

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## License

MIT
