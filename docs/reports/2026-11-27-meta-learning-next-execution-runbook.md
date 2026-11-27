# Runbook de execução — decisão e expansão do Meta-Learning

**Atualizado:** 27/11/2026  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`  
**Estado de entrada:** fases 1–4 concluídas; `metabasis_pilot_v1` congelada; avaliação LOO exploratória executada.  
**Objetivo desta rodada:** reproduzir o freeze e a avaliação LOO, validar os artefatos publicados e preparar uma decisão explícita sobre a Fase 5. Não executar ainda novas baterias GWO.

> **Mudança em relação ao runbook anterior:** as auditorias A–E, a validação do agregador, o freeze da meta-base e o primeiro LOO já foram executados e publicados nos dois commits mais recentes. Não repita a construção do freeze nem sobrescreva os resultados. Esta rodada é de reprodução independente e decisão.

## 1. Estado confirmado — não refazer

- 36 instâncias, 4 variantes GWO, 3 seeds pareadas: 432/432 execuções.
- Integridade: 432 chaves únicas; zero ausentes, extras ou duplicadas; zero valores numéricos inválidos.
- Normalização: UB publicado em 36/36 instâncias (`norm=ub`).
- Features: `taillard_pfsp_features_v1`, 35 preditores derivados apenas da matriz P.
- Freeze imutável: `experiments/meta_learning/data/metabasis_pilot_v1/`.
- LOO: 36 folds por instância, RF classifier e regressor, mais seletores fixos e aleatório.
- Resultado: RF não demonstrou ganho operacional útil sobre sempre Fuzzy. O regressor ficou praticamente empatado; o classificador foi pior.
- Nenhum holdout confirmatório foi reservado. Os resultados continuam exploratórios.

**Não execute:** `freeze_meta_learning_metabasis_pilot` sobre o diretório existente, expansão para 60/120, novas seeds, tuning, nem novas execuções das variantes GWO.

## 2. Interpretação que deve ser preservada

A métrica primária é regret por instância em relação ao melhor resultado observado naquela instância. Accuracy é complementar, pois 22/36 rótulos vencedores têm margem inferior a 0,5%.

| Seletor | Regret médio | IC95 bootstrap |
|---|---:|---:|
| Sempre Fuzzy | 0,0029187 | [0,0015889; 0,0044084] |
| RF regressor | 0,0029053 | [0,0015437; 0,0042979] |
| RF classifier | 0,0052324 | [0,0034233; 0,0070719] |
| Aleatório | 0,0090548 | [0,0071697; 0,0109805] |

A diferença pontual entre RF regressor e sempre Fuzzy é aproximadamente `-0.0000134`, sem evidência de ganho relevante: 28/36 empates no comparativo pareado, 5 vitórias e 3 derrotas do regressor. Os intervalos se sobrepõem amplamente. Não declarar superioridade do regressor.

Limitações:
- `n=36` instâncias independentes e 35 preditores: relação amostra/dimensão desfavorável e risco alto de sobreajuste.
- LOO não equivale a holdout externo; os conjuntos de treino dos folds se sobrepõem fortemente.
- O bootstrap sobre os 36 regrets descreve a dispersão entre instâncias deste piloto; não captura integralmente a variabilidade de treinamento/seleção do modelo.
- Três seeds estimam ruído de execução, não aumentam o número de instâncias independentes.
- Fuzzy é o melhor seletor operacional observado neste piloto, não um ótimo universal.

## 3. Preparação — confirmar estado do repositório

Na raiz:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log -2 --oneline
python --version
```

**Critério:** branch correta; registrar o HEAD e os dois commits mais recentes. Não descartar alterações locais. Se houver arquivos modificados, informe antes de continuar.

**Envie:** saída completa.

## 4. Etapa A — testes de integridade

```bash
python -m pytest -q tests/test_meta_learning_features.py tests/test_meta_learning_metabasis_pilot.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
```

**Critério:** todos os testes passam. Preserve warnings e traceback se houver falha.

**Envie:** saída completa do pytest.

## 5. Etapa B — verificar hashes do freeze

Execute na raiz. O script é somente leitura e compara os arquivos congelados com o manifesto:

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path

root = Path("experiments/meta_learning/data/metabasis_pilot_v1")
manifest = json.loads((root / "freeze_manifest.json").read_text(encoding="utf-8"))
print("SCHEMA", manifest["schema_version"])
print("N_INSTANCES", manifest["n_instances"])
print("N_RUNS", manifest["n_runs"])
print("FEATURE_VERSION", manifest["feature_version"])
print("PREDICTORS", len(manifest["predictor_columns"]))
for name, expected in manifest["hashes_sha256"].items():
    path = root / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    print(name, "OK" if actual == expected else "MISMATCH",
          "expected=", expected, "actual=", actual)
PY
```

**Critério:** schema `metabasis_pilot_v1`, 36 instâncias, 432 execuções, 35 preditores e quatro hashes iguais ao manifesto.

**Envie:** saída completa. Se algum hash divergir, pare; não regenere nem sobrescreva o freeze.

## 6. Etapa C — reproduzir o LOO em diretório novo

Não escreva sobre `selector_eval_exploratory_v1/`. Use um diretório de recheck:

```bash
python -m scripts.evaluate_meta_learning_selectors_pilot \
  --freeze-dir experiments/meta_learning/data/metabasis_pilot_v1 \
  --output results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127 \
  --seed 0 --random-repeats 100
```

PowerShell em uma linha:

```powershell
python -m scripts.evaluate_meta_learning_selectors_pilot --freeze-dir experiments/meta_learning/data/metabasis_pilot_v1 --output results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127 --seed 0 --random-repeats 100
```

**Critérios de reprodução aproximados:**
- 36 instâncias e 36 folds;
- accuracy classifier ≈ 0,2222; regressor ≈ 0,4722;
- regret médio RF classifier ≈ 0,005232;
- regret médio RF regressor ≈ 0,002905;
- regret médio sempre Fuzzy ≈ 0,002919;
- placar pareado RF regressor vs Fuzzy: 5 melhores / 3 piores / 28 empates.

Pequenas diferenças podem ocorrer apenas se ambiente/bibliotecas divergirem; registre versões e não ajuste seed para forçar igualdade.

**Envie:**
- saída completa do comando;
- `selector_eval_recheck_20261127/summary.json`;
- `selector_eval_recheck_20261127/per_instance_predictions.csv`.

## 7. Etapa D — confirmar versões do ambiente

```bash
python - <<'PY'
import sys, numpy, pandas, sklearn
print("python", sys.version)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scikit_learn", sklearn.__version__)
PY
```

**Envie:** saída. Ela será anexada à avaliação de reprodutibilidade.

## 8. Decisão pendente (aguardando escolha explícita)

A reprodução A–D foi executada e documentada em [2026-11-27-meta-learning-reproduction-ad.md](2026-11-27-meta-learning-reproduction-ad.md). Nenhuma opção abaixo foi selecionada ainda. Após a escolha, registrar a decisão em `docs/decisions/` antes de qualquer execução nova.

Opções:

1. **Continuar Meta-Learning com expansão de instâncias:** preparar `metabasis_v2`, priorizando diversidade e cobertura até 120 instâncias. Manter inicialmente 3–5 seeds pareadas para controlar custo; aumentar seeds depois se a variância por execução justificar. Reservar holdout por instância antes de qualquer tuning.
2. **Encerrar a extensão como resultado exploratório negativo/insuficiente:** documentar que, com 36 instâncias e 35 features, não houve ganho demonstrável sobre sempre Fuzzy. O projeto principal GWO continua completo.
3. **Reformular a pergunta de pesquisa:** por exemplo, seleção condicionada a orçamento/tempo, mas somente com decisão metodológica explícita e novo protocolo; não reutilizar os resultados como se medissem a nova pergunta.

**Minha recomendação metodológica atual:** se a extensão for mantida, expandir primeiro o número de instâncias, não apenas o número de seeds. Mais seeds refinam as médias por instância, mas não resolvem a limitação de apenas 36 unidades independentes. Não iniciar a expansão antes de aprovar o desenho, custo e holdout.

## 9. Registro de execução A–D

| Item | Resultado |
|---|---|
| Data | 2026-11-27 |
| Branch / HEAD | `recovery/surrogate-learning-curve-v2-oom` / `b5456d1f20523aca267c03ca379e58b3406c38fc` |
| Commits recentes | `b5456d1`, `5dec18e` |
| Python | 3.14.6 |
| NumPy / pandas / sklearn | 2.5.1 / 2.3.3 / 1.9.0 |
| Testes | 29 passed (2 warnings de deps externas) |
| Freeze hashes | 4/4 OK |
| LOO recheck | `selector_eval_recheck_20261127/`; `summary.json` idêntico ao publicado |
| Divergências | nenhuma |
| Pacote A–D | completo (prep, testes, hashes, LOO, versões) |
| Relatório | [2026-11-27-meta-learning-reproduction-ad.md](2026-11-27-meta-learning-reproduction-ad.md) |
| JSON | `selector_eval_recheck_20261127/reproduction_record.json` |
| Decisão Fase 5 | **pendente** (escolher §8 opção 1, 2 ou 3; nenhuma pré-selecionada) |

Working tree limpa no início da rodada. Freeze não foi regenerado. Artefatos publicados não foram sobrescritos.

## 10. Documentos de referência

- [Relatório da reprodução A–D](2026-11-27-meta-learning-reproduction-ad.md)
- [Status das fases](2026-11-27-meta-learning-phase-status.md)
- [Avaliação LOO exploratória](2026-11-27-meta-learning-selector-loo-exploratory.md)
- [Decisão de freeze](../decisions/2026-11-27-metabasis-pilot-v1-freeze.md)
- [Roadmap de conclusão](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [README de Meta-Learning](../../experiments/meta_learning/README.md)
