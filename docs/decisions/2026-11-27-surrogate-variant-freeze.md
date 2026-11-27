# Decisão: congelar a variante Surrogate para a meta-base

**Data:** 2026-11-27  
**Status:** aprovada  
**Gate:** Fase 2 do roadmap de Meta-Learning

## Decisão

Manter a variante Surrogate histórica da Semana 6 sem troca de arquitetura nem retuning silencioso:

1. Modelo: `MLPRegressor` 64×64 no pipeline Week 4 (`normalized_job_rank_permutation`).
2. Uso online: prever a geração inteira; reavaliar exatamente o top-3; atualizar líderes/convergência **somente** com fitness exato.
3. Artefatos Week 6 (`ta001`, `ta011`): `results/week4_surrogate_v2/<instance>/surrogate.joblib`.
4. Artefato do piloto de distribuição `ta111`: Cost Pilot v2  
   `results/meta_learning_cost_pilot_v2/surrogates/ta111/surrogate.joblib`  
   (SHA-256 registrado em `results/gwo_population_distribution_audit_v1/metadata.json`). Identidade distinta da Week 6; não misturar protocolos.
5. Novas instâncias da meta-base: treinar um surrogate **por instância** com o protocolo Week 4 congelado (`scripts/run_week4_surrogate.py`), gravar hash/métricas, e só então executar a variante.

## Evidência

| Fonte | Conclusão |
|---|---|
| Comparação MLP/RF/ET/HGB em permutações uniformes (`surrogate_model_comparison_protocol.md`) | HGB melhora RMSE/Spearman, mas recall top-3/top-10 permanece 0. Nenhum modelo é seletor confiável. |
| Ranking dentro de gerações GWO reais (`surrogate_ranking_on_gwo_summary.json`) | No trajeto Surrogate/Baseline em `ta111`, Spearman médio ~0.03–0.08; mediana de recall top-3 = 0.0. Utilidade operacional fraca. |
| Diversidade das populações | Entropia posicional colapsa tarde; candidatos quase-clones. Ranking top-k fica mais difícil e mais sensível a erro. |

Qualidade global (RMSE) e utilidade top-k são perguntas distintas. Nenhuma troca de modelo resolveu a segunda nestes pilotos.

## Limitações explícitas

- A variante Surrogate permanece na meta-base como configuração histórica instrumentada, não como otimizador com ranking confiável.
- Orçamento exato continua desigual: 1.530 avaliações exatas + 15.000 previsões vs 15.030 avaliações exatas nas demais.
- Não alegar superioridade do Surrogate sem reportar custo e a falha de ranking.
- Não substituir MLP por HGB/RF durante a construção da meta-base confirmatória.

## Verificação

- Testes de `gwo_pfs_surrogate`: previsões não entram em líderes/convergência.
- Hashes de modelo/instância obrigatórios em metadados de qualquer bateria nova.
- Este documento é a especificação congelada até nova decisão versionada.
