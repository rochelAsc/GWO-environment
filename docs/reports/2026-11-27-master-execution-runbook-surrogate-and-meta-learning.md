# Runbook mestre — bateria de Surrogate e Meta-Learning

**Data de referência:** 27/11/2026  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`  
**Objetivo:** executar, em ordem controlada, as investigações pendentes do surrogate de makespan e concluir a avaliação do Meta-Learning que seleciona variantes GWO.  
**Regra central:** preservar os resultados existentes, executar somente etapas autorizadas pelos gates e nunca misturar os dois problemas experimentais.

> Este runbook consolida o estado documentado no repositório nesta data. É um plano operacional: uma fase só passa a `concluída` quando seus artefatos, hashes, testes e relatório forem inspecionados. Não executar comandos de geração de dados sobre diretórios já preenchidos sem verificar a política de retomada do respectivo runner.

## 0. Mapa dos dois trilhos

| Trilho | Unidade de previsão/decisão | Pergunta | Estado de entrada |
|---|---|---|---|
| A — Surrogate de makespan | Permutação de jobs | O modelo estima makespan e ordena candidatos suficientemente bem para apoiar a busca? | Curva 300–32.000 concluída; piloto de comparação de modelos concluído em uma única condição; ainda sem evidência para integração ao GWO. |
| B — Meta-Learning de variantes | Instância PFSP/Taillard | Qual variante GWO (Baseline, Optuna, Fuzzy ou Surrogate) deve ser escolhida para uma instância nova? | Split de 120 congelado; checkpoint 60 development concluído (48 instâncias, 576 runs); decisão 60→120 pendente. |

**Não confundir:**
- O surrogate prediz o makespan de uma permutação.
- O Meta-Learner prediz qual variante GWO tende a funcionar melhor em uma instância.
- Candidatos/permutacões de uma trajetória GWO não são instâncias independentes e não aumentam o tamanho amostral da meta-base.
- Nenhuma etapa deste runbook altera a formulação PFSP, substitui GWO ou reabre as Semanas 2–6.

## 1. Estado inicial e artefatos que devem permanecer imutáveis

### 1.1 Surrogate

- Curva original: `results/meta_learning_surrogate_learning_curve_v2_full/`.
- Extensão recuperada: `results/meta_learning_surrogate_learning_curve_v2_extension_recovered/`.
- Dados completos da extensão: `results/meta_learning_surrogate_learning_curve_v2_extension/`.
- Análise consolidada 300–32.000: [surrogate_learning_curve_v2_extension_statistical_analysis.md](../../experiments/meta_learning/reports/surrogate_learning_curve_v2_extension_statistical_analysis.md).
- Protocolo de comparação de modelos: [surrogate_model_comparison_protocol.md](../../experiments/meta_learning/reports/surrogate_model_comparison_protocol.md).
- Protocolo v2: [surrogate_learning_curve_v2_protocol.md](../../experiments/meta_learning/reports/surrogate_learning_curve_v2_protocol.md).
- Auditoria matemática v2: [surrogate_learning_curve_v2_mathematical_audit.md](../../experiments/meta_learning/reports/surrogate_learning_curve_v2_mathematical_audit.md).

Não sobrescrever, renomear ou regenerar os conjuntos de teste, os NPZs de treino, os CSVs de runs/summaries ou os resultados recuperados. Qualquer nova bateria usa diretório de saída novo e registra hashes dos arquivos de origem.

### 1.2 Meta-Learning

- Freeze piloto v1: `experiments/meta_learning/data/metabasis_pilot_v1/` — imutável.
- Split v2: `experiments/meta_learning/data/metabasis_v2/split_manifest.csv` — imutável; SHA-256 registrado no relatório de status.
- Checkpoint 60 development: `results/meta_learning_metabasis_v2/checkpoint60_dev/` — 576 runs, 48 instâncias.
- Holdout de 12 instâncias do estágio 60: selado, não executado.
- Decisão, checkpoint e inventário: links no [README Meta-Learning](../../experiments/meta_learning/README.md).

Não regenerar inventário/split nem modificar `metabasis_pilot_v1`. Não ler, agregar, executar ou consultar targets do holdout antes do gate confirmatório.

## 2. Ordem global recomendada

1. **S-A0 — auditoria de entrada e integridade** dos artefatos do surrogate e do Meta-Learning.
2. **S-A1 — corrigir/validar métricas top-k**, incluindo empates e definição inequívoca de regret; adicionar testes antes de qualquer comparação ampliada.
3. **S-A2 — completar comparação pareada de modelos** em dados idênticos, com repetições e duas instâncias.
4. **S-A3 — investigar distribuição de candidatos reais do GWO**, sem misturar esse teste com o teste uniforme já existente.
5. **S-A4 — decidir arquitetura/representação e integração**; não integrar automaticamente.
6. **M-B0 — decisão formal 60→120**, usando apenas custo, integridade e desenvolvimento.
7. **M-B1 — se aprovado, completar development stage=120**; holdout continua selado.
8. **M-B2 — congelar pipeline de seleção** (features, modelos, hiperparâmetros, baselines, métricas, código e hashes).
9. **M-B3 — executar uma única abertura do holdout** (24 instâncias se 120; ou 12 se a decisão formal encerrar em 60).
10. **M-B4 — relatório final, auditoria, reprodução e apresentação**, mantendo conclusões negativas/inconclusivas quando os dados assim indicarem.

As trilhas A e B podem ser desenvolvidas em paralelo documentalmente, mas não devem disputar memória/CPU durante execuções pesadas. Recomenda-se concluir uma execução longa por vez.

---

# PARTE A — SURROGATE DE MAKESPAN

## A0. Auditoria de entrada

Antes de executar:
- confirmar branch e commit;
- confirmar que os três diretórios de resultados da §1.1 existem e não foram alterados;
- validar presença de `learning_curve_runs.csv`, `learning_curve_summary.csv`, metadados e conjuntos de teste;
- verificar hashes dos NPZs de treino/teste contra os metadados do piloto;
- verificar que `ta071` e `ta111` correspondem aos arquivos Taillard versionados;
- verificar espaço em disco e memória disponível;
- copiar os logs de ambiente e o comando exato para o relatório da nova execução.

**Gate A0:** qualquer divergência de hash, instância, dimensão ou teste fixo interrompe a bateria. Não “corrigir” o arquivo de origem; investigar e criar novo artefato versionado.

## A1. Métricas top-k: contrato obrigatório

A implementação atual documentada na curva v2 usa `argsort` e escolhe exatamente k índices. Para makespan, empates são plausíveis. A regra de desempate pode alterar recall e regret. Além disso, o campo `topk_regret` atual é a diferença entre o melhor makespan dentro do conjunto previsto e o melhor makespan real do teste; não é o regret médio dos k selecionados.

Antes da comparação ampliada, formalizar e testar:

1. **Ranking global:** Spearman e Kendall tau-b, mantendo a convenção atual.
2. **Conjunto real top-k:** declarar como os empates no limite k são tratados. Recomendação: reportar duas visões — (a) top-k estrito determinístico, com ordenação estável e chave secundária pelo índice original; (b) top-k inclusivo, incluindo todos os candidatos empatados com o valor na posição k. Não comparar resultados calculados com políticas diferentes.
3. **Conjunto previsto top-k:** aplicar política equivalente e determinística aos valores previstos.
4. **Recall:** interseção entre conjuntos real e previsto dividida pelo tamanho do conjunto real usado naquela política. No modo inclusivo, explicitar denominador variável.
5. **Best-selected regret:** `min(y_selected) - min(y_test)`; gap do melhor candidato escolhido.
6. **Mean-selected regret:** `mean(y_selected) - min(y_test)`; qualidade média dos selecionados.
7. **Mean selected makespan:** média exata de makespan dos candidatos selecionados.
8. **Baseline aleatório:** estimar distribuição de recall/regret ao selecionar k candidatos aleatoriamente, com seed e número de repetições documentados.

Adicionar testes unitários para: empate no limite k, todos os valores iguais, k=1, k maior que n, previsão constante, ordenação inversa, candidato ótimo selecionado e nenhum ótimo selecionado. Testar também invariância a permutação da ordem das linhas quando a chave estável é preservada.

**Gate A1:** funções de métrica com docstrings e contrato, testes passando, CSVs contendo nomes que distingam `best_selected_regret` de `mean_selected_regret`. Não sobrescrever métricas antigas: conservar os resultados históricos e produzir uma reavaliação versionada quando houver NPZs suficientes.

## A2. Comparação de modelos — bateria ampliada

### Pergunta

Mantendo exatamente os mesmos dados de treino e teste, um modelo alternativo melhora a qualidade de ordenação/seleção em relação ao MLP 64×64?

### Matriz recomendada

| Fator | Valores |
|---|---|
| Instâncias | `ta071` (100×10), `ta111` (500×20) |
| N | 8.000 e 32.000 |
| Repetições | 5 |
| Amostragem principal | Uniforme, usando conjuntos já persistidos |
| Modelos | MLP 64×64, RandomForest, ExtraTrees, HistGradientBoosting |
| Teste | conjunto fixo de 1.000 permutações por instância |
| Execução | CPU, um modelo por vez, uma thread quando suportada |

A matriz completa contém 2 instâncias × 2 tamanhos × 5 repetições × 4 modelos = **80 ajustes**. O piloto já executado (ta111, N=8.000, repetição 1) é evidência exploratória e não substitui as demais células. Se os dados persistidos não cobrirem todas as combinações de N/repetição com o mesmo teste fixo, não inventar ou reconstruir silenciosamente os arrays: registrar lacuna e gerar apenas os conjuntos ausentes em uma etapa de preparação com hash/seed explícitos.

Hiperparâmetros iniciais estão congelados no [protocolo de comparação](../../experiments/meta_learning/reports/surrogate_model_comparison_protocol.md). Não fazer tuning com o teste. Qualquer tuning posterior usa validação interna derivada apenas do treino e constitui uma etapa separada.

### Execução segura

1. Executar testes do runner e das métricas.
2. Executar um único ajuste em `ta111`, N=8.000, para medir RSS, tempo e checkpoint.
3. Verificar que todos os modelos recebem arrays de treino/teste idênticos por célula.
4. Executar a matriz restante sequencialmente, com checkpoint por modelo e por célula.
5. Confirmar retomada sem duplicar chaves.
6. Persistir CSV bruto por ajuste, resumo agregado, metadados, logs e hashes.
7. Calcular diferenças pareadas entre modelos somente quando o mesmo conjunto de treino, repetição e teste for compartilhado.

### Métricas a reportar

- RMSE, MAE, R²;
- Spearman, Kendall tau-b;
- recall top-3/top-10/top-50 com política de empate explícita;
- best-selected regret e mean-selected regret;
- média do makespan dos selecionados;
- tempo de treino, inferência em lote e por amostra;
- RSS máximo do processo e tamanho serializado do modelo.

A métrica de decisão não pode ser RMSE isolado. O propósito é priorizar boas permutações. Mostrar resultados por instância e por repetição; com duas instâncias, as conclusões são locais/exploratórias.

### Critério de decisão A2

- Se um modelo melhorar de forma consistente ranking e regret, sem custo operacional proibitivo, selecioná-lo apenas como candidato a uma validação posterior.
- Se os modelos tiverem resultados próximos, não escalar N automaticamente: passar à análise de representação e distribuição.
- Se RMSE/Spearman melhorarem sem melhorar top-k/regret, registrar que o ganho preditivo global não se converteu em utilidade de seleção.
- Não declarar um vencedor com base em uma repetição ou em uma única métrica.

## A3. Distribuição de candidatos reais do GWO

A avaliação uniforme mede generalização em permutações aleatórias. O GWO pode visitar uma distribuição muito diferente. Esta é uma hipótese prioritária antes de integrar qualquer surrogate online.

### Protocolo

1. Identificar e congelar quais populações/traces GWO serão usados, versões de algoritmo, instâncias, variantes e seeds.
2. Calcular SHA-256 dos CSVs/artefatos de população e validar schema, duplicatas e integridade.
3. Separar por instância/execução/seed; não tratar linhas da mesma trajetória como unidades independentes.
4. Construir amostras de candidatos por estágio da busca (inicial, intermediário, final), se os dados permitirem.
5. Descrever distribuição de permutações: diversidade, duplicatas, distância Kendall, frequência posicional, precedência par-a-par, diversidade entre indivíduos e evolução temporal.
6. Comparar essa distribuição com a uniforme e com os dados de treino atuais.
7. Criar teste de avaliação próprio, por execução/seed ou blocos de trajetória, sem vazamento entre treino e teste.
8. Rotular por makespan exato os candidatos selecionados para diagnóstico; documentar custo.
9. Avaliar os modelos com as métricas A1 e comparar a utilidade de seleção com a distribuição uniforme.

**Atenção:** candidatos de uma mesma população são correlacionados. Intervalos/testes estatísticos devem agrupar por execução/seed ou trajetória; não usar cada linha como observação independente.

### Gate A3

Só considerar uso online se:
- a distribuição operacional estiver caracterizada;
- o teste representar candidatos de execuções não usadas no treino;
- o surrogate melhorar a seleção de candidatos sob essa distribuição;
- custo de erro, falso positivo e avaliação exata estiver quantificado;
- fallback seguro para avaliação exata estiver definido.

## A4. Decisão de integração

Não substituir a implementação congelada da variante Surrogate nem alterar os resultados das Semanas 2–6 por causa de um piloto. Se a evidência for positiva, propor experimento isolado com feature flag, orçamento fixo, fallback exato e comparação pareada com GWO sem surrogate. Se inconclusiva/negativa, documentar e manter o surrogate como investigação.

**Não iniciar N=64.000/128.000 por enquanto.** A curva até 32.000 melhora, mas a comparação de modelos e a discrepância entre ranking global e recuperação dos melhores candidatos precisam ser resolvidas primeiro.

---

# PARTE B — META-LEARNING DE SELEÇÃO DE VARIANTES GWO

## B0. Estado e decisão 60→120

O checkpoint 60 development está concluído:
- 48 instâncias de desenvolvimento;
- 576/576 runs (432 reutilizadas do piloto v1 após hash check + 144 novas);
- 12 instâncias do holdout stage=60 não executadas;
- Fuzzy venceu 20/48; regret médio 0,0037; 30/48 rótulos low-confidence;
- custo observado das 12 novas: aproximadamente 0,33 h.

A decisão formal 60→120 ainda precisa ser registrada. Ela deve usar apenas:
- integridade e completude;
- cobertura por grupo/dimensão;
- qualidade/proveniência dos arquivos;
- variabilidade e qualidade dos targets de development;
- custo medido e disponibilidade de hardware/tempo.

Não usar qualquer resultado do holdout para decidir.

### Opção B0-1 — encerrar em 60

- Usar as 48 instâncias development para CV agrupada.
- Congelar todo o pipeline.
- Abrir uma única vez as 12 instâncias holdout stage=60.
- A avaliação será pequena e exploratória; não exagerar a força confirmatória.

### Opção B0-2 — avançar para 120

- Executar somente development stage=120: 48 instâncias × 4 variantes × 3 seeds = **576 runs**.
- Não executar nem abrir holdout durante essa etapa.
- Ao final: 96 development (1.152 runs) + 24 holdout seladas.
- Congelar pipeline antes de executar as 24 × 4 × 3 = **288 runs** do holdout.

A decisão deve ser registrada em novo documento em `docs/decisions/` antes da bateria correspondente.

## B1. Completar development stage=120 (condicional)

Pré-requisitos:
- decisão formal aprovada;
- split manifesto e hashes conferidos;
- runner v2 e testes aprovados;
- diretório de resultados correto;
- confirmação de que o comando opera apenas na partição development.

Comando já documentado:

```bash
python -m pytest -q tests/test_meta_learning_metabasis_v2_split.py tests/test_meta_learning_metabasis_v2_runner.py
python -m scripts.run_meta_learning_metabasis_v2 --stages 120 --partitions development
```

Depois:
- verificar 576 novas combinações esperadas;
- validar zero missing, extra e duplicadas;
- confirmar hashes das instâncias e modelos Surrogate;
- confirmar ausência total de holdout nos dados de execução;
- agregar 96 instâncias development;
- registrar runtime por instância/variante, falhas e retomadas;
- preservar checkpoint 60 e todos os CSVs anteriores.

## B2. Treinamento e validação do Meta-Learner

Unidade estatística = instância. Divisões nunca podem separar seeds da mesma instância entre treino e teste.

Comparar:
1. seleção aleatória;
2. sempre Baseline;
3. sempre Optuna;
4. sempre Fuzzy (baseline operacional prioritário);
5. sempre Surrogate;
6. melhor variante global calculada apenas dentro do fold de treino;
7. RandomForestClassifier;
8. RandomForestRegressor com seleção pela menor previsão.

Regras:
- CV agrupada por instância no development (GroupKFold/LOO conforme plano e tamanho);
- tuning, seleção de features, calibração e limiar somente dentro dos folds;
- classificação e regressão usam exatamente as mesmas divisões;
- reportar rótulos low-confidence e análise de sensibilidade;
- não tratar 3 seeds como 3 instâncias;
- não usar ID, hash, grupo, nome, partição, UB/LB, makespan, winner ou seed como preditores;
- features preditivas somente da matriz de processamento P, conforme freeze `taillard_pfsp_features_v1`.

Métricas:
- classificação: balanced accuracy, macro-F1, matriz de confusão, recall por classe, log loss/Brier se houver probabilidades;
- regressão: MAE/RMSE por alvo, R² com cautela, erro de ranking;
- seleção: regret por instância contra o oráculo retrospectivo, regret vs sempre Fuzzy, vitórias/derrotas/empates, média/mediana e IC;
- operação: runtime, custo de preparação, número de avaliações e custo de inferência.

O orçamento desigual permanece explícito: Baseline/Optuna/Fuzzy usam 15.030 avaliações exatas; Surrogate usa 1.530 avaliações exatas + 15.000 previsões, além de preparação. Não declarar igualdade de orçamento.

## B3. Freeze antes do holdout

Antes de abrir holdout, gerar um manifesto contendo:
- hash do split e dos dados de development;
- versão/commit do extrator e lista ordenada das features;
- tratamento de missing/escala;
- modelos e hiperparâmetros;
- folds e seeds;
- baselines e regra de melhor global;
- métrica primária e métricas secundárias;
- definição de regret e tratamento de empates;
- código de treino e avaliação com hashes;
- versões de Python e bibliotecas;
- critérios de sucesso e limitações previstas.

O freezer v2 deve recusar sobrescrita. Não reutilizar freezer piloto v1 sem suporte explícito ao schema v2.

## B4. Holdout confirmatório — uma única abertura

- Se encerrou em 60: 12 instâncias e 144 runs (4 variantes × 3 seeds × 12).
- Se completou 120: 24 instâncias e 288 runs (4 × 3 × 24).
- Executar em etapa isolada e com protocolo congelado.
- Não fazer tuning nem selecionar modelos com holdout.
- Reportar todos os resultados, inclusive resultados desfavoráveis.
- Se houver mudança de protocolo após observar holdout, ele deixa de ser confirmatório; será necessário novo conjunto independente para uma nova alegação confirmatória.

Comando de holdout só deve ser executado depois de confirmar a sintaxe e o gate do runner; não adicionar flags presumidas. A opção `--allow-holdout` não deve ser usada antes do freeze formal.

---

# PARTE C — CHECKLIST OPERACIONAL DE CADA SESSÃO

## Antes de iniciar

- [ ] Confirmar branch e commit.
- [ ] Fazer `git status` e confirmar que não há alterações locais não salvas.
- [ ] Ler o protocolo específico da fase.
- [ ] Confirmar diretório de saída novo ou política explícita de retomada.
- [ ] Conferir hashes/manifestos de entradas.
- [ ] Conferir espaço em disco, RAM e energia/rede se notebook remoto.
- [ ] Registrar comando, parâmetros, seeds e horário de início.
- [ ] Executar testes direcionados.
- [ ] Confirmar que a execução não acessará holdout nem sobrescreverá artefatos congelados.

## Durante a execução

- [ ] Monitorar CPU, RAM, disco e crescimento de arquivos.
- [ ] Verificar checkpoints e logs periodicamente.
- [ ] Não interromper apenas porque uma célula parece lenta; comparar com estimativa do piloto.
- [ ] Se interromper, preservar diretório e logs; não apagar outputs parciais.
- [ ] Registrar motivo, última chave concluída e procedimento de retomada.
- [ ] Não rodar processos pesados concorrentes no mesmo ambiente.

## Depois da execução

- [ ] Confirmar estado final do runner e contagem esperada/observada.
- [ ] Verificar missing, extra, duplicatas, NaN/Inf e warnings.
- [ ] Recalcular hashes de entradas e saídas críticas.
- [ ] Rodar testes e agregadores.
- [ ] Inspecionar tabelas e gráficos, não apenas status `completed`.
- [ ] Atualizar relatório com resultados reais, limitações e decisão.
- [ ] Fazer commit dos scripts/documentos/artefatos pequenos; para dados grandes, registrar localização, hash e instrução de obtenção.
- [ ] Enviar relatório, logs, manifestos e outputs relevantes para revisão.

## Pacote mínimo para revisão

1. SHA do commit/branch.
2. Comando exato executado.
3. Saída dos testes.
4. Manifesto/metadata.
5. CSV bruto e resumo.
6. Hashes dos arquivos de entrada e saída.
7. Log de execução e status/checkpoint.
8. Resumo de missing/extra/duplicadas.
9. Tempo, RAM e espaço em disco.
10. Decisões pendentes e qualquer desvio do protocolo.

## Política de interrupção e retomada

- Nunca apagar a pasta de uma execução interrompida.
- Nunca reutilizar um diretório parcial como se fosse resultado completo.
- Retomar apenas se o runner validar configuração, hashes e chaves existentes.
- Se houver mudança de código/protocolo, iniciar novo diretório e registrar a relação com a execução anterior.
- Distinguir tempo original de execução de tempo de recuperação; não misturar tempos de geração reconstruídos com tempos originais.
- Após falha de integridade, interromper e diagnosticar antes de continuar.

---

# PARTE D — CRITÉRIOS DE CONCLUSÃO

## Surrogate

- [ ] Métricas top-k corrigidas/testadas e históricas preservadas.
- [ ] Comparação de modelos pareada concluída (80 ajustes ou desvios justificados).
- [ ] Resultados por instância/repetição, ICs e custos reportados.
- [ ] Distribuição GWO real caracterizada e avaliada em teste separado.
- [ ] Decisão explícita sobre arquitetura/representação/integração.
- [ ] Nenhuma integração no GWO sem gate operacional e fallback exato.

## Meta-Learning

- [ ] Decisão 60→120 documentada.
- [ ] Se 120: development stage=120 concluído e validado.
- [ ] Meta-base congelada com hashes e proveniência.
- [ ] CV agrupada e baselines executados sem vazamento.
- [ ] Holdout aberto uma única vez após freeze.
- [ ] Regret vs sempre Fuzzy e incerteza reportados.
- [ ] Relatório final e reprodução completos.

## Projeto principal

- [ ] Resultados obrigatórios do GWO continuam separados das extensões.
- [ ] Conclusões negativas/inconclusivas são mantidas, sem ajustar retrospectivamente o protocolo.
- [ ] Referências novas são registradas em `experiments/meta_learning/referencias.md` e citadas na seção em que fundamentam decisões.
- [ ] README, roadmap, status das fases e runbooks refletem o estado real.

## Referências internas

- [README Meta-Learning](../../experiments/meta_learning/README.md)
- [Runbook da expansão metabasis_v2](2026-11-27-meta-learning-next-execution-runbook.md)
- [Roadmap de conclusão](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [Status das fases](2026-11-27-meta-learning-phase-status.md)
- [Checkpoint 60 development](2026-11-27-meta-learning-v2-checkpoint60-dev.md)
- [Análise estatística da curva surrogate](../../experiments/meta_learning/reports/surrogate_learning_curve_v2_extension_statistical_analysis.md)
- [Protocolo de comparação de modelos](../../experiments/meta_learning/reports/surrogate_model_comparison_protocol.md)
- [Referências bibliográficas](../../experiments/meta_learning/referencias.md)
