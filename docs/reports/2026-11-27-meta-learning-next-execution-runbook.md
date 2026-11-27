# Runbook de execução — próxima etapa do Meta-Learning

**Data:** 27/11/2026  
**Branch de referência:** `recovery/surrogate-learning-curve-v2-oom`  
**Estado inicial:** Fases 1–4 concluídas; 36 instâncias, 4 variantes, 3 seeds, 432 execuções agregadas.  
**Objetivo desta rodada:** auditar e congelar a meta-base piloto antes de implementar/treinar os seletores meta.

> **Importante:** execute as etapas na ordem e envie as saídas indicadas ao final de cada bloco. Não avance para expansão de 60/120 instâncias nem para uma bateria maior de seeds nesta rodada. O resultado de 36 instâncias é exploratório.

## 1. Escopo e decisões que não devem mudar nesta rodada

- O problema continua sendo PFSP/Taillard minimizando makespan.
- As quatro opções continuam sendo variantes GWO existentes: `baseline`, `optuna`, `fuzzy`, `surrogate`.
- Meta-Learning escolhe uma variante GWO para uma instância; não substitui GWO nem prevê permutações.
- A unidade independente é a **instância**. As 3 seeds são repetições para estimar ruído, não 108 amostras independentes.
- Features permitidas: somente estatísticas calculadas da matriz de processamento P, conforme `taillard_pfsp_features_v1`. Identificadores, hashes, caminho, UB/LB, makespan, seed e resultados GWO são metadados/alvos, nunca preditores.
- Não retunar nem substituir o MLP da variante Surrogate congelada. Registrar separadamente seu orçamento: 1.530 avaliações exatas + 15.000 previsões, contra 15.030 avaliações exatas das outras variantes.
- Não interpretar “Fuzzy venceu 17/36” como superioridade universal. O baseline operacional a superar é **sempre Fuzzy**, calculado também dentro de cada fold de treino quando usado como comparador aprendido.
- Não ajustar features ou hiperparâmetros consultando o holdout.

## 2. Diagnóstico que motiva esta rodada

O relatório do piloto aponta 36 instâncias, 432 execuções, 17 vitórias Fuzzy, 9 Baseline, 9 Optuna e 1 Surrogate; 22/36 rótulos têm margem inferior a 0,5%. Isso torna o regret por instância e a comparação contra seletores fixos tão importantes quanto accuracy.

Há três pontos que precisam ser verificados antes de treinar:

1. O agregador atual `scripts/analyze_meta_learning_metabasis_pilot.py` agrupa resultados, mas não valida explicitamente todas as combinações esperadas de instância × variante × seed, duplicatas, valores não finitos ou divergências com o manifesto.
2. A normalização usa UB quando disponível e, caso contrário, melhor média observada na própria instância. Precisamos inspecionar a coluna `norm` e a cobertura de UB. Se houver mistura, médias globais de `y` não devem ser interpretadas como uma escala comum; regret por instância continua sendo a métrica principal de seleção.
3. A base derivada e as features precisam ter cobertura 1:1 por instância, sem colunas de metadados entrando nos preditores.

Esta rodada primeiro reproduz e caracteriza o estado atual. Depois que você enviar os resultados, a próxima alteração de código será implementar validação rigorosa e testes do agregador, antes de treinar qualquer modelo.

## 3. Preparação — confirmar repositório e ambiente

Na raiz do repositório:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
python --version
```

**Critério:** branch `recovery/surrogate-learning-curve-v2-oom`, working tree compreensível e commit registrado. Se houver alterações locais não commitadas, não as descarte; informe quais são.

**Envie:** saída dos quatro comandos. Se estiver em outra branch, pare e informe antes de continuar.

## 4. Etapa A — executar testes de contratos já existentes

```bash
python -m pytest -q tests/test_meta_learning_features.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
```

Se algum teste falhar, não tente corrigir por conta própria nesta rodada: envie o traceback completo. Não rode a bateria completa do projeto ainda; estes testes verificam os contratos diretamente envolvidos.

**Critério:** todos os testes passam. Warnings devem ser preservados na saída, não ocultados.

**Envie:** saída completa do pytest, incluindo contagem de testes e warnings.

## 5. Etapa B — reexecutar a agregação sem sobrescrever o resultado publicado

O script atual aceita caminhos explícitos. Gere uma reprodução em diretório novo, preservando `analysis/` já publicado:

```bash
python -m scripts.analyze_meta_learning_metabasis_pilot \
  --runs results/meta_learning_metabasis_pilot_v1/runs.csv \
  --manifest experiments/meta_learning/data/instance_manifest.csv \
  --output results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127
```

No PowerShell, o mesmo comando pode ser executado em uma linha:

```powershell
python -m scripts.analyze_meta_learning_metabasis_pilot --runs results/meta_learning_metabasis_pilot_v1/runs.csv --manifest experiments/meta_learning/data/instance_manifest.csv --output results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127
```

**Critério esperado para reprodução:** `N_INST 36`, `N_RUNS 432`, mesmas contagens de vitórias e métricas do relatório vigente, salvo diferenças explicáveis por alterações de arquivo/commit. A reprodução não substitui a validação de completude da Etapa C.

**Envie:** saída completa do comando e os dois arquivos gerados:
- `results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/summary.json`
- `results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/per_instance_targets.csv`

## 6. Etapa C — auditoria independente da estrutura dos dados

Execute este bloco Python a partir da raiz. Ele é somente leitura: não modifica os CSVs. Salve a saída em texto.

```bash
python - <<'PY'
import csv
from collections import Counter

runs_path = "results/meta_learning_metabasis_pilot_v1/runs.csv"
manifest_path = "experiments/meta_learning/data/instance_manifest.csv"
targets_path = "results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/per_instance_targets.csv"

with open(runs_path, newline="", encoding="utf-8") as f:
    runs = list(csv.DictReader(f))
with open(manifest_path, newline="", encoding="utf-8") as f:
    manifest = list(csv.DictReader(f))
with open(targets_path, newline="", encoding="utf-8") as f:
    targets = list(csv.DictReader(f))

variants = {"baseline", "optuna", "fuzzy", "surrogate"}
instances = {r["instance"] for r in manifest}
expected = {(i, v, str(seed)) for i in instances for v in variants for seed in (0, 1, 2)}
keys = [(r["instance"], r["variant"], r["seed"]) for r in runs]
counts = Counter(keys)
observed = set(keys)
norm_counts = Counter(r.get("norm", "") for r in targets)
ub_missing = [r["instance"] for r in manifest if not r.get("upper_bound", "").strip()]
target_instances = {r["instance"] for r in targets}

print("RUN_ROWS", len(runs))
print("MANIFEST_INSTANCES", len(instances))
print("VARIANTS", sorted({r["variant"] for r in runs}))
print("SEEDS", sorted({r["seed"] for r in runs}))
print("UNEXPECTED_VARIANTS", sorted({r["variant"] for r in runs} - variants))
print("MISSING_KEYS", len(expected - observed))
print("EXTRA_KEYS", len(observed - expected))
print("DUPLICATE_KEYS", sum(n - 1 for n in counts.values() if n > 1))
print("ROWS_PER_INSTANCE_VARIANT", sorted(Counter((r["instance"], r["variant"]) for r in runs).values()))
print("TARGET_ROWS", len(targets))
print("TARGET_INSTANCE_COVERAGE_MISSING", sorted(instances - target_instances))
print("TARGET_INSTANCE_COVERAGE_EXTRA", sorted(target_instances - instances))
print("NORMALIZATION_COUNTS", dict(norm_counts))
print("MANIFEST_WITHOUT_UB", sorted(ub_missing))
print("RUNS_WITH_EMPTY_INSTANCE_HASH", sum(not r.get("instance_sha256", "").strip() for r in runs))
print("RUNS_WITH_EMPTY_SURROGATE_MODEL_HASH", sum(r["variant"] == "surrogate" and not r.get("model_sha256", "").strip() for r in runs))
PY
```

Se estiver no PowerShell e o here-document não funcionar no terminal utilizado, rode o bloco no terminal Bash/WSL ou salve-o temporariamente como `scripts/_audit_meta_pilot_local.py` e execute `python scripts/_audit_meta_pilot_local.py`. Não versione esse arquivo temporário.

**Resultados esperados, a confirmar e não presumir:**
- 432 linhas em `runs.csv`;
- 36 instâncias no manifesto e na tabela derivada;
- exatamente quatro variantes e seeds `0, 1, 2`;
- 12 linhas por instância (4 variantes × 3 seeds);
- zero chaves ausentes, extras ou duplicadas;
- zero instâncias faltando/sobrando na tabela de alvos;
- hash de instância preenchido em todas as execuções;
- hash de modelo preenchido nas execuções Surrogate;
- a distribuição de `norm` deve ser compatível com a cobertura real de UB. Se aparecer `rel_best`, reportar quantas instâncias usam cada regra; não comparar médias globais como se a escala fosse homogênea.

Se algum contador divergir, **pare aqui**. Não treine modelos nem tente “consertar” o CSV manualmente. Envie a saída para localizarmos a origem.

**Envie:** saída completa do bloco.

## 7. Etapa D — verificar consistência numérica e alvos

Ainda em modo somente leitura, execute:

```bash
python - <<'PY'
import csv, math

paths = {
    "runs": "results/meta_learning_metabasis_pilot_v1/runs.csv",
    "targets": "results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/per_instance_targets.csv",
}
for name, path in paths.items():
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print("\n", name.upper(), "rows=", len(rows))
    numeric_fields = (
        ["best_makespan", "runtime_seconds", "exact_evaluations", "surrogate_predictions"]
        if name == "runs" else
        ["margin_y", "mean_baseline", "mean_optuna", "mean_fuzzy", "mean_surrogate",
         "y_baseline", "y_optuna", "y_fuzzy", "y_surrogate"]
    )
    for field in numeric_fields:
        if field not in rows[0]:
            print(field, "MISSING_COLUMN")
            continue
        vals = []
        invalid = 0
        for row in rows:
            try:
                value = float(row[field])
                if not math.isfinite(value):
                    invalid += 1
                else:
                    vals.append(value)
            except (TypeError, ValueError):
                invalid += 1
        print(field, "invalid=", invalid,
              "min=", min(vals) if vals else None,
              "max=", max(vals) if vals else None)
PY
```

**Critério:** nenhuma métrica numérica ausente/não finita; makespan e runtime positivos; contadores de avaliações não negativos. Valores de makespan acima do UB publicado não são, isoladamente, erro: o UB é referência conhecida, não garantia de que toda execução heurística o alcance.

**Envie:** saída completa. Se houver `MISSING_COLUMN` ou valores inválidos, pare e envie também o cabeçalho do arquivo.

## 8. Etapa E — verificar alinhamento entre features e alvos

Confirme que os arquivos estão presentes:

```bash
python -c "from pathlib import Path; paths=['experiments/meta_learning/data/instance_features.csv','results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/per_instance_targets.csv','experiments/meta_learning/data/instance_manifest.csv']; [print(p, Path(p).exists(), Path(p).stat().st_size if Path(p).exists() else None) for p in paths]"
```

Depois envie os cabeçalhos (primeira linha) e contagem de registros de features e alvos:

```bash
python - <<'PY'
import csv
for path in [
    "experiments/meta_learning/data/instance_features.csv",
    "results/meta_learning_metabasis_pilot_v1/analysis_recheck_20261127/per_instance_targets.csv",
]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print("\nFILE", path)
        print("COLUMNS", reader.fieldnames)
        print("ROWS", len(rows))
        print("INSTANCE_UNIQUE", len({r.get("instance") for r in rows}))
PY
```

**Critério:** uma linha por instância em cada arquivo, 36 instâncias, identificadores compatíveis e nenhum campo de resultado/identificador/hash/path/UB/LB incluído no conjunto de preditores. Os metadados podem continuar nos CSVs; a separação será aplicada no pipeline de treinamento.

**Envie:** saída completa e, se possível, os dois CSVs. Não remova colunas manualmente.

## 9. O que ainda NÃO executar

Até revisar suas saídas, não execute:

- expansão para 60 ou 120 instâncias;
- aumento para 10, 20 ou 30 seeds;
- treinamento de RandomForest;
- tuning de hiperparâmetros;
- seleção de features olhando o dataset inteiro;
- avaliação em holdout ainda não reservado;
- qualquer nova execução das variantes GWO.

Motivo: primeiro precisamos provar completude, integridade, escala dos alvos e alinhamento das features. Treinar antes disso pode produzir métricas aparentemente boas sobre uma base inconsistente ou com vazamento.

## 10. Próximo trabalho após você enviar os resultados

Após receber as saídas das Etapas A–E, a sequência de implementação será:

1. adicionar validação explícita de schema, instâncias, variantes, seeds, chaves únicas, valores numéricos, hashes e cobertura ao agregador;
2. adicionar testes unitários para CSV completo, linha ausente, duplicata, variante inválida, seed inesperada, valor não finito e manifesto incompleto;
3. definir e registrar formalmente o tratamento de normalização por UB versus `rel_best`; reportar regret por instância como métrica primária de seleção;
4. congelar `metabasis_pilot_v1` com manifesto, hashes e proveniência;
5. implementar baselines e validação agrupada por instância, primeiro como análise exploratória;
6. somente depois treinar RF classifier/regressor, comparando-os com sempre Fuzzy e os demais seletores fixos.

### Baselines e avaliação que serão implementados depois

- aleatório uniforme (repetido com seeds próprias e reportado como distribuição);
- sempre Baseline, sempre Optuna, sempre Fuzzy e sempre Surrogate;
- melhor variante global calculada somente no treino de cada fold;
- RandomForestClassifier;
- RandomForestRegressor (multioutput ou quatro modelos, decisão técnica documentada).

Métricas primárias: regret por instância, média/mediana do regret, intervalo de confiança e comparação pareada com sempre Fuzzy. Accuracy, balanced accuracy, macro-F1, matriz de confusão, MAE/RMSE e qualidade do ranking serão métricas complementares. Toda divisão será por instância; nenhuma instância pode aparecer simultaneamente em treino e teste.

## 11. Pacote que você deve me devolver

Envie, de preferência em um único upload ou resposta:

1. saída de preparação (branch, commit, Python);
2. saída integral do pytest;
3. saída da reexecução do agregador;
4. `summary.json` e `per_instance_targets.csv` da pasta `analysis_recheck_20261127`;
5. saídas das Etapas C, D e E;
6. eventuais erros/tracebacks completos.

Com isso, consigo fazer a auditoria cruzada e implementar a próxima parte com base em evidências, sem pedir que você rode uma bateria grande desnecessária.

## 12. Registro de execução

Preencher após a execução local:

| Item | Resultado |
|---|---|
| Data/hora | PREENCHER |
| Branch / commit | PREENCHER |
| Python | PREENCHER |
| Testes | PREENCHER |
| Agregação reproduzida | PREENCHER |
| Completude das chaves | PREENCHER |
| Integridade numérica | PREENCHER |
| Alinhamento features/alvos | PREENCHER |
| Decisão | Aguardando auditoria |

