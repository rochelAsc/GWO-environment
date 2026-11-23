# Semana 3 — Status da reconstrução

**Status:** implementação inicial preparada; execução experimental pendente.

## Decisões congeladas

- Formulação: PFSP Taillard, minimização do makespan.
- Baseline: results/week2_baseline_v1.
- Orçamento: 15.030 avaliações por execução.
- TPE: 30 trials, sampler seed 20261123.
- Seeds de sintonia: 100, 101 e 102.
- Seeds de avaliação final: 0–29, pareadas com a baseline e não usadas na sintonia.
- Espaço: população {9, 10, 15, 18, 30, 45}; a_start [1,5; 2,5]; a_end [0; 0,5]; expoente [0,5; 2,0].
- Instâncias: ta001 e ta011.

## Arquivos

- scripts/gwo_pfs.py: schedule configurável com defaults compatíveis com a Semana 2.
- scripts/tune_week3_optuna.py: TPE, banco SQLite, CSV de trials e gráficos.
- scripts/run_week3_evaluation.py: avaliação congelada e comparação pareada.
- tests/test_week3_optuna.py: testes do schedule e do orçamento.
- docs/reports/week3_optuna_protocol.md: protocolo experimental.

## Validação ainda necessária

1. Instalar dependências do requirements.txt.
2. Executar testes completos.
3. Executar sintonia de 30 trials.
4. Inspecionar melhor configuração, histórico e importância.
5. Executar avaliação final com 30 seeds.
6. Auditar CSVs, metadados, orçamento e comparação pareada.
7. Só então marcar a Semana 3 como concluída.

Nenhum resultado experimental da Semana 3 é declarado neste documento.
