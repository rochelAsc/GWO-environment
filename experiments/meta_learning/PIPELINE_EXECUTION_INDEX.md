# Índice operacional — Surrogate e Meta-Learning

**Data de referência:** 27/11/2026  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`

Este é o ponto de entrada para executar as baterias pendentes. Leia primeiro o [Runbook mestre](../../docs/reports/2026-11-27-master-execution-runbook-surrogate-and-meta-learning.md), que define ordem, gates, critérios de parada, retomada e o pacote de evidências a enviar após cada etapa.

## 1. Próximas ações em ordem

| Ordem | Ação | Estado |
|---:|---|---|
| 1 | Auditar hashes, branch, dados e ambiente antes de novas execuções | Pendente por sessão |
| 2 | Corrigir/validar métricas top-k com empates e duas definições de regret | Pendente |
| 3 | Completar comparação pareada dos 4 modelos em ta071/ta111, N=8k/32k, 5 repetições | Pendente; piloto isolado já existe |
| 4 | Caracterizar candidatos das trajetórias reais do GWO e avaliar surrogate nessa distribuição | Pendente |
| 5 | Decidir se existe evidência para integração experimental do surrogate | Bloqueado até 2–4 |
| 6 | Formalizar decisão Meta-Learning: encerrar em 60 ou avançar a 120 | Pendente |
| 7 | Se 120: coletar somente development stage=120 (576 runs) | Condicional |
| 8 | Treinar/validar seletores em desenvolvimento e congelar pipeline | Pendente |
| 9 | Abrir holdout uma única vez, após freeze | Bloqueado |
| 10 | Relatório final, auditoria e reprodução | Pendente |

## 2. Documentos por função

### Coordenação e execução

- [Runbook mestre — as duas baterias](../../docs/reports/2026-11-27-master-execution-runbook-surrogate-and-meta-learning.md)
- [Runbook específico metabasis_v2](../../docs/reports/2026-11-27-meta-learning-next-execution-runbook.md)
- [Roadmap de conclusão](../../docs/plans/2026-11-27-meta-learning-completion-roadmap.md)
- [Status das fases](../../docs/reports/2026-11-27-meta-learning-phase-status.md)

### Surrogate de makespan

- [Protocolo de amostragem v2](reports/surrogate_learning_curve_v2_protocol.md)
- [Auditoria matemática v2](reports/surrogate_learning_curve_v2_mathematical_audit.md)
- [Análise estatística consolidada 300–32k](reports/surrogate_learning_curve_v2_extension_statistical_analysis.md)
- [Protocolo de comparação de modelos](reports/surrogate_model_comparison_protocol.md)
- [Referências bibliográficas](referencias.md)

### Meta-Learning de seleção de variantes GWO

- [Decisão de expansão v2](../../docs/decisions/2026-11-27-meta-learning-expansion-v2.md)
- [Inventário e split congelado](../../docs/reports/2026-11-27-meta-learning-v2-phase-a-inventory-split.md)
- [Checkpoint 60 development](../../docs/reports/2026-11-27-meta-learning-v2-checkpoint60-dev.md)
- [Freeze piloto v1](../../docs/decisions/2026-11-27-metabasis-pilot-v1-freeze.md)
- [README metodológico](README.md)

## 3. Estado que não pode ser confundido

- Curva surrogate: dados de treino até 32.000 permutações, duas instâncias, LHS e uniforme; conclusão estatística não demonstra que o surrogate já seleciona os melhores candidatos com qualidade operacional.
- Comparação de modelos: piloto observado em ta111/N=8.000/repetição 1; não equivale à matriz ampliada de 80 ajustes prevista no runbook mestre.
- Meta-Learning: checkpoint 60 development concluído com 48 instâncias e 576 runs; 12 instâncias de holdout permanecem seladas; a decisão 60→120 está pendente.
- A meta-base de seleção de variantes e o dataset de treinamento do surrogate são objetos diferentes e nunca devem ser combinados.

## 4. Regra de atualização

Ao terminar uma fase:
1. atualizar o relatório específico com dados observados;
2. registrar commit, comando, ambiente, hashes e contagens;
3. atualizar o status das fases e este índice;
4. atualizar o README metodológico se houver mudança de protocolo/conclusão;
5. adicionar referências somente quando novas fontes tiverem sido efetivamente consultadas;
6. não marcar etapa concluída sem artefato verificável.

Não execute uma etapa bloqueada apenas porque o comando está documentado. A autorização vem do gate metodológico correspondente.
