# Registro de decisão — expansão do estudo GWO/PFSP

- **Data:** 2026-11-27
- **Status:** aprovada pelo autor para orientar as próximas etapas
- **Commit de referência anterior:** `dd4ef1aa7a702588e7e01b23f93025126eea5d25`
- **Protocolo consolidado:** [Roteiro experimental GWO/PFSP](../research/gwo_pfsp_experimental_roadmap_2026-11-27.md)

## Decisões aprovadas

1. Manter como problema principal o PFSP clássico de uma fábrica, minimizando makespan.
2. Manter GWO como objeto central. Random Keys permanece como linha de base a investigar; variantes discretas, híbridas e adaptativas serão estudadas sem misturar resultados de problemas diferentes.
3. Pausar Meta-Learning até construir uma base experimental ampla e confiável. Não foi descartado.
4. Selecionar 120 instâncias Taillard por estratificação em 12 classes; dividir em 72 instâncias de desenvolvimento (6 por classe) e 48 de holdout (4 por classe). IDs finais serão gerados aleatoriamente com seed fixa a partir do inventário validado.
5. Usar o conjunto de desenvolvimento para diagnóstico, seleção de mecanismos, tuning, sensibilidade e ablação. Reservar o holdout para avaliação confirmatória após congelamento do método e protocolo.
6. Investigar Baseline, Optuna, Fuzzy e Surrogate de maneira equilibrada, além de mecanismos GWO discretos/híbridos/adaptativos e baselines NEH/IG quando viáveis.
7. Comparar métodos sob orçamento de **avaliações exatas da função objetivo**. Iterações são métricas secundárias. Previsões do Surrogate e custos de treino/inferência terão contadores separados.
8. Usar checkpoints de orçamento derivados de Fibonacci, inicialmente com multiplicadores `1, 2, 3, 5, 8` sobre um orçamento-base (B_0) calibrado no piloto. O multiplicador 13 é opcional, condicionado à viabilidade. Não executar todos os níveis automaticamente.
9. Piloto: 10 → 20 → 30 seeds cumulativas; desenvolvimento: 20 → 30 → 40 seeds cumulativas; avaliação final: começar com 40 seeds e aumentar em blocos se a precisão estatística pré-definida for insuficiente.
10. Definir a regra de precisão, largura desejada dos intervalos, bloco de expansão e teto máximo de seeds depois do piloto, mas antes do holdout. Não interromper porque um resultado favorece um algoritmo ou atinge significância.
11. Validar individualmente as quatro estratégias: diversidade/convergência para GWO; separação de tuning e avaliação para Optuna; ablações de entradas para Fuzzy; validação por permutação e reavaliação exata para Surrogate.
12. Usar Friedman, Wilcoxon pareado, Holm, intervalos de confiança, tamanhos de efeito e análise por instância/classe, respeitando que seeds não são instâncias independentes.
13. Só retomar Meta-Learning após a base experimental e usar validação agrupada por instância.
14. Considerar VRF como benchmark complementar futuro, após a fase Taillard. Generalização para outras classes de problemas é direção posterior.

## Consequências

- O protocolo antigo não é sobrescrito; resultados históricos permanecem vinculados aos seus protocolos e escopos originais.
- A seleção 72/48, a escada absoluta de orçamento e a regra final de precisão ainda dependem, respectivamente, do inventário real e dos dados do piloto.
- Nenhuma bateria confirmatória deve começar antes de auditar parser, hashes, contadores, logs e reprodutibilidade.
- O roteiro consolidado é um plano aprovado, não evidência de que a nova bateria já foi executada.

