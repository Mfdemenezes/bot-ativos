#!/bin/bash
cd ~/bot-ativos || exit 1
git pull -q
mkdir -p logs

# Para processos antigos
pkill -f scheduler.py 2>/dev/null
pkill -f monitor.py 2>/dev/null
sleep 2

# Inicia scheduler
.venv/bin/python scheduler.py > logs/scheduler.log 2>&1 &
SCHED_PID=$!
echo "Scheduler iniciado: PID $SCHED_PID"

# Inicia monitor
.venv/bin/python monitor.py > logs/monitor.log 2>&1 &
MON_PID=$!
echo "Monitor iniciado: PID $MON_PID"

sleep 2
ps -p $SCHED_PID,$MON_PID && echo "✅ Ambos rodando" || echo "❌ Erro ao iniciar"
