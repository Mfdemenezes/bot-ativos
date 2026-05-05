# Spec: Bot Análise de Ativos

## Objetivo
Sistema de análise técnica de ativos (B3 + NYSE) com alertas de compra/venda via Telegram.

## Componentes principais
- `src/data_fetcher.py` — busca OHLCV via yfinance
- `src/liquidity_engine.py` — Smart Money Concepts (BSL/SSL, FVG, sweeps)
- `src/volume_profile.py` — POC, VAH, VAL, VWAP, delta de volume
- `src/price_action.py` — indicadores técnicos via pandas-ta, order blocks
- `src/ai_forecast.py` — previsão probabilística com Amazon Chronos
- `src/signal_generator.py` — ensemble scorer (0-100), gera sinal + targets + stop
- `src/analyzer.py` — orquestrador
- `main.py` — FastAPI endpoint `/analyze/{ticker}`
- `scheduler.py` — APScheduler rodando após fechamento B3 e NYSE

## Lógica de sinal
Score composto:
- Sweep de liquidez: ±40 pts
- Estrutura de mercado: ±15 pts
- FVG: ±20 pts
- VWAP: ±10 pts
- Volume Profile POC: ±15 pts
- RSI: ±10 pts
- Chronos forecast: ±10 pts

COMPRA se score ≥ 55, VENDA se score ≤ -55, senão AGUARDAR.

## Infraestrutura
- Docker Compose (API + Scheduler + PostgreSQL)
- Oracle Cloud VM A1.Flex (ARM)
- Alertas via Telegram Bot API
