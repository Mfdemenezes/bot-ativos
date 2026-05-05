# Bot Ativos

Análise técnica avançada de ativos B3 e NYSE com alertas via Telegram.

## Componentes
- **Liquidity Engine** — BSL/SSL, FVG, sweeps, equal highs/lows (Smart Money)
- **Volume Profile** — POC, VAH, VAL, VWAP, delta
- **Price Action** — estrutura de mercado, order blocks, indicadores (RSI, MACD, BB, ATR)
- **AI Forecast** — Amazon Chronos (zero-shot) com fallback EMA
- **Signal Generator** — ensemble scorer com R:R automático
- **Notifier** — alertas formatados no Telegram

## Setup rápido (Oracle)
```bash
git clone git@github.com:Mfdemenezes/bot-ativos.git
cd bot-ativos
cp .env.example .env
# edite .env com seus tokens
./setup.sh
```

## Uso
```bash
# Analisar ativo
curl http://localhost:8000/analyze/PETR4.SA

# Com parâmetros
curl "http://localhost:8000/analyze/AAPL?period=3mo&interval=1h"
```

## Watchlist automática
Edite `watchlist.json` — o scheduler roda após fechamento B3 (17h30) e NYSE (21h30).

## Variáveis de ambiente
Ver `.env.example`
