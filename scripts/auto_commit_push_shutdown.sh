
#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$HOME/GWO-environment-auto-shutdown.log"
TARGET_TIME="20:30:00"

exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

abort() {
    log "ERRO: $*"
    exit 1
}

cd "$REPO_DIR"

log "Agendamento iniciado."
log "Repositório: $REPO_DIR"
log "Desligamento previsto: hoje às 20:30."

# Não permite execução em detached HEAD.
BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || abort "Nenhuma branch ativa."

# Confere o remoto.
git remote get-url origin >/dev/null 2>&1 ||
    abort "Remoto origin não configurado."

# Calcula o tempo restante até hoje às 20:30.
TARGET_TIMESTAMP="$(date -d "today $TARGET_TIME" +%s)"
CURRENT_TIMESTAMP="$(date +%s)"

if (( CURRENT_TIMESTAMP >= TARGET_TIMESTAMP )); then
    abort "O horário das 20:30 já passou. Nenhuma alteração foi enviada."
fi

REMAINING=$((TARGET_TIMESTAMP - CURRENT_TIMESTAMP))

log "Aguardando até 20:30."
log "Tempo restante: $((REMAINING / 60)) minutos."

# Autenticação antecipada para o desligamento.
sudo -v || abort "Falha na autenticação sudo."

# Mantém sudo válido durante a espera.
(
    while true; do
        sleep 30
        sudo -n -v || exit 1
    done
) &
KEEPALIVE_PID=$!

cleanup() {
    kill "$KEEPALIVE_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep "$REMAINING"

log "Horário de execução atingido."

# Não inicia o Git enquanto a recuperação estiver ativa.
while pgrep -f '[r]ecover_surrogate_learning_curve_v2' >/dev/null; do
    log "Recuperação ainda em execução. Aguardando 60 segundos..."
    sleep 60
done

log "Recuperação finalizada."

# Confirma branch e estado do repositório.
BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || abort "Branch não identificada."

log "Adicionando alterações ao Git."
git add -A

if ! git diff --cached --quiet; then
    COMMIT_MESSAGE="chore: save surrogate recovery results $(date +%Y-%m-%d)"
    log "Criando commit: $COMMIT_MESSAGE"
    git commit -m "$COMMIT_MESSAGE"
else
    log "Nenhuma alteração nova para commit."
fi

# Publica explicitamente a branch atual.
log "Enviando $BRANCH para origin."
git push origin "$BRANCH"

log "Push concluído com sucesso."

# Última verificação da autenticação sudo.
sudo -n -v || abort "Autenticação sudo expirou. Não desligando."

log "Desligamento agendado para daqui a 1 minuto."
sudo -n shutdown -h +1

