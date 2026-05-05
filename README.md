# 📈 Bot Ativos

Bot de análise técnica avançada de ativos da B3 e NYSE com alertas automáticos via Telegram.

## ✅ Status atual

| Componente | Status |
|---|---|
| Coleta de dados (yfinance) | ✅ Funcionando |
| Liquidity Engine (SMC) | ✅ Funcionando |
| Volume Profile (POC/VAH/VAL/VWAP) | ✅ Funcionando |
| Price Action (Order Blocks, RSI, MACD, BB, ATR) | ✅ Funcionando |
| Multi-Timeframe (1d + 4h + 1h) | ✅ Funcionando |
| Sentimento via RSS (Yahoo + Google News) | ✅ Funcionando |
| Signal Generator (ensemble scorer) | ✅ Funcionando |
| Banco de dados (SQLite / PostgreSQL) | ✅ Funcionando |
| FastAPI endpoint `/analyze/{ticker}` | ✅ Funcionando |
| Scheduler automático (B3 17h30 + NYSE 21h30) | ✅ Funcionando |
| Alertas Telegram | ✅ Funcionando (requer token) |
| Amazon Chronos AI (previsão probabilística) | ⚙️ Opcional — instalar separado |
| Docker Compose (Oracle ARM) | ✅ Pronto para deploy |

## 🧠 Como funciona

O sinal é gerado por um ensemble de 9 componentes com score de 0 a 100:

| Componente | Peso | Descrição |
|---|---|---|
| Multi-Timeframe | ±35 pts | Sinal só válido se 2/3 timeframes concordam |
| Sweep de Liquidez | ±30 pts | BSL/SSL varado com fechamento oposto |
| FVG (Fair Value Gap) | ±15 pts | Imbalância de preço aberta |
| Estrutura de Mercado | ±10 pts | HH+HL (alta) ou LH+LL (baixa) |
| Volume Profile POC | ±10 pts | Preço no ponto de maior volume |
| VWAP | ±8 pts | Desconto/prêmio institucional |
| RSI | ±8 pts | Sobrevendido/sobrecomprado |
| Sentimento RSS | ±9 pts | Notícias Yahoo Finance + Google News |
| Chronos AI | ±8 pts | Previsão probabilística P10/P50/P90 |

**Threshold:** score ≥ 60 → COMPRA | score ≤ -60 → VENDA | senão → AGUARDAR

## 🗂️ Estrutura

```
bot-ativos/
├── src/
│   ├── analyzer.py          # orquestrador principal
│   ├── data_fetcher.py      # coleta OHLCV via yfinance
│   ├── liquidity_engine.py  # BSL/SSL, FVG, sweeps, equal highs/lows
│   ├── volume_profile.py    # POC, VAH, VAL, VWAP, delta de volume
│   ├── price_action.py      # indicadores técnicos + order blocks
│   ├── multi_timeframe.py   # alinhamento 1d + 4h + 1h
│   ├── sentiment.py         # sentimento via RSS gratuito
│   ├── ai_forecast.py       # Amazon Chronos (fallback EMA)
│   ├── signal_generator.py  # ensemble scorer → sinal + targets + stop
│   ├── notifier.py          # alertas Telegram formatados
│   └── database.py          # persistência SQLite/PostgreSQL
├── main.py                  # FastAPI
├── scheduler.py             # APScheduler (roda após fechamento B3/NYSE)
├── watchlist.json           # ativos monitorados
├── docker-compose.yml       # API + Scheduler + PostgreSQL
├── Dockerfile               # otimizado para Oracle ARM (A1.Flex)
└── setup.sh                 # deploy com um comando
```

## 🚀 Deploy na Oracle

```bash
git clone git@github.com:Mfdemenezes/bot-ativos.git
cd bot-ativos
cp .env.example .env
nano .env   # preenche TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID
./setup.sh
```

## 🧪 Teste rápido (sem Docker)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -c "
from src.analyzer import analyze
import json
r = analyze('PETR4.SA', notify=False)
print(r['signal'], r['confidence'], r['reasons'])
"
```

## 📡 API

```bash
# Analisar ativo
curl http://localhost:8000/analyze/PETR4.SA
curl http://localhost:8000/analyze/AAPL

# Com parâmetros
curl "http://localhost:8000/analyze/VALE3.SA?period=3mo&interval=4h&notify=false"
```

Resposta:
```json
{
  "ticker": "PETR4.SA",
  "price": 49.34,
  "signal": "VENDA",
  "confidence": 63,
  "target1": 29.14,
  "stop": 50.02,
  "rr": 29.53,
  "structure": "LATERAL",
  "mtf": { "diário": "VENDA", "4h": "NEUTRO", "1h": "VENDA", "consensus": "VENDA" },
  "sentiment": { "direction": "bullish", "articles": 120 }
}
```

## ⚙️ Instalar Chronos AI (opcional, melhor acurácia)

```bash
.venv/bin/pip install chronos-forecasting torch
```

O modelo `chronos-t5-large` é baixado automaticamente na primeira execução (~1.5GB).

## 📋 Watchlist padrão

Edite `watchlist.json` para adicionar/remover ativos:

```json
{
  "br": ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "WEGE3.SA"],
  "us": ["AAPL", "NVDA", "TSLA", "SPY", "QQQ"]
}
```

O scheduler roda automaticamente após o fechamento de cada mercado.

## 💰 Custo

**R$ 0,00** — tudo gratuito: yfinance, pandas-ta, Chronos (local), Telegram Bot API, Oracle Always Free, GitHub.
