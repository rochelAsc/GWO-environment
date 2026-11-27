# Runbook de execução — expansão Meta-Learning para metabasis_v2

**Atualizado:** 27/11/2026  
**Branch:** recovery/surrogate-learning-curve-v2-oom  
**Decisão:** aprovada em [2026-11-27-meta-learning-expansion-v2.md](../decisions/2026-11-27-meta-learning-expansion-v2.md)  
**Estado de entrada:** metabasis_pilot_v1 congelada e reprodução A–D aprovada.  
**Objetivo:** preparar e executar, em etapas auditáveis, a expansão de 36 para 60 e, se viável, 120 instâncias Taillard, com holdout por instância reservado antes de observar novos resultados.

> **Importante:** este runbook substitui o runbook de reprodução/decisão anterior. A reprodução A–D já terminou. Não repetir testes/LOO apenas por seguir este documento. A decisão de expansão foi aprovada, mas a coleta v2 ainda não foi executada. A primeira etapa é adaptar a infraestrutura, pois alguns scripts atuais ainda estão fixados no piloto v1.

## 1. Estado confirmado e invariantes

- metabasis_pilot_v1: 36 instâncias, 432 execuções (4 variantes × 3 seeds), 35 preditores, congelamento SHA-256 4/4 verificado.
- LOO exploratório reproduzido bit a bit; RF regressor não demonstrou ganho operacional útil sobre sempre Fuzzy.
- O piloto tem 36 unidades independentes e 35 preditores; é desenvolvimento, não holdout.
- O projeto principal continua GWO para PFSP/Taillard. Meta-Learning seleciona entre Baseline, Optuna, Fuzzy e Surrogate; não substitui o GWO.
- metabasis_pilot_v1 e seus resultados permanecem imutáveis.

**Não fazer:** sobrescrever o freeze v1; abrir o holdout durante desenvolvimento; retunar GWO/Surrogate; alterar features; misturar resultados de trilhos diferentes; executar a bateria v2 antes do gate técnico da §4.

## 2. Desenho da expansão

### 2.1 Tamanho e estratificação

O benchmark-alvo tem 12 grupos de dimensão e 10 instâncias por grupo (120). Confirmar o inventário completo e sua proveniência antes de assumir essa cobertura.

| Estágio | Desenvolvimento | Holdout selado | Total |
|---|---:|---:|---:|
| 60 instâncias | 48 (4/grupo) | 12 (1/grupo) | 60 |
| 120 instâncias | 96 (8/grupo) | 24 (2/grupo) | 120 |

As 36 instâncias de metabasis_pilot_v1 pertencem ao desenvolvimento. Em cada grupo, das 7 instâncias ainda não usadas, selecionar 5 para desenvolvimento e 2 para holdout, com seed de split fixada e sem observar qualquer resultado de algoritmo. Acrescentar ao manifesto um campo stage. Entre as 5 de desenvolvimento, sortear 1 para stage=60 e 4 para stage=120; entre as 2 de holdout, sortear 1 para stage=60 e 1 para stage=120. Assim, no checkpoint de 60 entram 1 desenvolvimento + 1 holdout por grupo; ao avançar para 120, entram mais 4 desenvolvimento + 1 holdout por grupo.

O manifesto de split deve ser criado e congelado antes da primeira execução GWO v2. Registrar: ID, grupo, origem, SHA-256, dimensões, bounds, partição, estágio (60/120), seed/algoritmo de split e hash do manifesto. Não usar makespan, winner, UB/LB ou resultados GWO na seleção do split.

### 2.2 Regra para abrir o holdout

- Se encerrar em 60: abrir as 12 instâncias uma única vez, depois de congelar pipeline, features, modelos, hiperparâmetros, baselines e critérios.
- Se avançar para 120: manter as 12 instâncias do checkpoint de 60 completamente seladas e não consultar seus targets. Ao completar 120, abrir uma única vez o holdout final de 24.
- Não usar holdout para escolher features, ajustar hiperparâmetros, selecionar modelo ou decidir entre 60 e 120.

O checkpoint 60 serve para validar custo, cobertura e integridade. A decisão de avançar deve usar apenas desenvolvimento e métricas operacionais, nunca desempenho dos targets de holdout.

### 2.3 Variantes, seeds e orçamento

- Variantes congeladas: baseline, optuna, fuzzy, surrogate.
- Seeds iniciais pareadas: [0, 1, 2] em todas as variantes e instâncias.
- 60 instâncias: 720 execuções totais; 288 novas além das 432 do piloto.
- 120 instâncias: 1.440 execuções totais; 1.008 novas além do piloto.
- Não aumentar seeds sem evidência de que a variância intra-instância limita as estimativas.
- Preservar o orçamento desigual: Baseline/Optuna/Fuzzy = 15.030 avaliações exatas; Surrogate = 1.530 exatas + 15.000 previsões por execução, mais preparação. Não alegar igualdade de orçamento.

Estimativa de planejamento baseada no piloto: aproximadamente 1,06 h para 36×3 seeds; extrapolação linear simples ≈1,8 h para 60×3 e ≈3,5 h para 120×3. Não é SLA nem previsão garantida: registrar runtime por grupo, pois as instâncias maiores podem alterar o custo.

## 3. Organização dos artefatos

Manter separado do piloto:

~~~text
results/
└── meta_learning_metabasis_v2/
    ├── runs.csv
    ├── metadata.json
    ├── surrogates/
    ├── inventory/
    ├── split/
    ├── analysis/
    └── checkpoints/

experiments/meta_learning/data/
└── metabasis_v2/
    ├── instance_features.csv
    ├── per_instance_targets.csv
    ├── instance_manifest.csv
    ├── split_manifest.csv
    └── freeze_manifest.json
~~~

O diretório v2 deve ser criado novo. Nunca copiar outputs analíticos do piloto como se fossem resultados v2. As linhas brutas de execução do piloto podem ser incorporadas à base de desenvolvimento somente após auditoria de compatibilidade e com proveniência histórica explícita; preservar o freeze original e seus hashes. Holdout não pode conter nenhuma das 36 instâncias do piloto.

## 4. Gate técnico obrigatório — adaptar scripts antes da coleta

A inspeção do código atual encontrou acoplamento explícito ao piloto:

- scripts/run_meta_learning_metabasis_pilot.py grava protocol=meta_learning_metabasis_pilot_v1 nos metadados, embora aceite --instances, --seeds e --output.
- scripts/analyze_meta_learning_metabasis_pilot.py tem defaults v1 e valida por padrão seeds [0,1,2]; aceita caminhos customizados, mas deve ser testado com manifesto v2 e 60/120 instâncias.
- scripts/freeze_meta_learning_metabasis_pilot.py grava schema_version=metabasis_pilot_v1 e usa defaults do piloto. **Não usar esse freezer para v2 sem generalização e testes.**
- O extrator atual pode gerar features a partir de diretório, mas o manifesto precisa preservar bounds, hash, grupo e split sem contaminar os preditores.

### 4.1 Alterações necessárias

1. Generalizar ou criar runner v2 com identificador de protocolo meta_learning_metabasis_v2, retomada segura, validação de linhas existentes e registro de configuração/commit/ambiente.
2. Generalizar agregador para aceitar paths v2, manifesto e seeds; garantir validação de todas as chaves esperadas, sem assumir 36 instâncias.
3. Criar etapa determinística de inventário e split; validar 12 grupos, 5/7/10 instâncias por grupo conforme o estágio e ausência de sobreposição entre desenvolvimento e holdout.
4. Generalizar freezer para schema metabasis_v2, incluir split manifesto e hashes, recusar sobrescrita e não alterar o freezer v1.
5. Adicionar testes para split, vazamento, retomada, duplicatas, linhas ausentes, hash divergente, alinhamento features/targets e recusa de sobrescrita.
6. Garantir que metadados (instance, hash, grupo, partição, bounds, seed, winner, makespan, caminho) nunca entrem nos 35 preditores.

### 4.2 Critério de aceite técnico

- Testes novos e antigos passam.
- O runner retoma uma execução interrompida sem duplicar chaves.
- A validação detecta falta/duplicação de qualquer combinação instância × variante × seed.
- O split é determinístico e reproduzível a partir do manifesto/seed.
- O freezer v2 gera schema e hashes próprios e recusa sobrescrever diretório existente.
- Um teste pequeno (1–2 instâncias fora do piloto, em diretório temporário) comprova integração sem contaminar resultados reais.

**Não executar a bateria de 60 antes de este gate ser aprovado.**

## 5. Fase A — inventário completo e pré-registro do split

1. Obter os arquivos Taillard faltantes a partir da fonte espelho documentada em data/benchmarks/taillard/README.md; manter formato original e registrar proveniência.
2. Inventariar o conjunto de 120 esperado: 12 grupos × 10 instâncias. Confirmar IDs, dimensões, bounds disponíveis e hashes. Não presumir que um arquivo é válido apenas pelo nome.
3. Revalidar os 36 arquivos já usados contra os hashes registrados; não alterá-los.
4. Em cada grupo, separar as 3 instâncias do piloto das 7 restantes. Com seed fixada, sortear 5 novas para desenvolvimento e 2 para holdout; sortear também a ordem dentro de cada partição para atribuir stage=60 (1 desenvolvimento + 1 holdout) e stage=120 (4 desenvolvimento + 1 holdout).
5. Congelar o manifesto e seu SHA-256 antes de observar novos resultados GWO.
6. Gerar features determinísticas das instâncias elegíveis. Features do holdout podem ser extraídas da matriz P (são entradas disponíveis na inferência), mas seus targets e resultados de GWO devem permanecer selados.

**Aceite:** inventário validado, cobertura 10 por grupo, 36 piloto identificadas como desenvolvimento, seleção determinística e manifesto versionado/hash registrado.

**Envie para revisão:** resumo do inventário por grupo, manifesto de split, hash do manifesto, lista de arquivos com hash/proveniência e relatório de bounds ausentes.

## 6. Fase B — preparar dados de desenvolvimento do checkpoint 60

1. Preparar a base bruta v2 com as 36 linhas históricas de desenvolvimento e as 12 novas instâncias de desenvolvimento.
2. Reutilizar os 432 resultados do piloto somente após comparar hash da instância, variante, seed, configuração, versão do código e definição de métricas. Marcar source=pilot_v1_reused; não alterar os arquivos congelados.
3. Executar somente as 12 instâncias novas de desenvolvimento com 3 seeds × 4 variantes = 144 novas execuções. Total combinado: 48 × 3 × 4 = 576 linhas de desenvolvimento.
4. Não executar ou consultar os 12 holdouts neste checkpoint se houver intenção de continuar para 120.
5. Gerar features/manifesto, agregar os resultados e validar completude, chaves, hashes, bounds e contadores.
6. Manter o output em results/meta_learning_metabasis_v2/; registrar custos reais por grupo/variante.

**Aceite:** 48 instâncias de desenvolvimento completas (576 runs), 12 holdouts selados, zero duplicatas/ausências, 35 preditores válidos e proveniência completa.

> Nota: 720 runs é a contagem do checkpoint de 60 incluindo 144 execuções de holdout. No fluxo de desenvolvimento, só 576 runs são executados/abertos antes da decisão final. As 144 execuções de holdout ficam adiadas até a avaliação final se o estudo encerrar em 60.

## 7. Checkpoint de decisão — avançar para 120 ou encerrar em 60

Com base somente em desenvolvimento, custo e integridade:

- verificar distribuição de instâncias por grupo, diversidade de features e ausência de duplicatas;
- revisar custo real por grupo, extrapolar o custo restante e avaliar disponibilidade de tempo/hardware;
- revisar falhas de execução, variabilidade por seed e qualidade dos alvos;
- manter o holdout completamente fechado.

**Avançar para 120** se a coleta estiver íntegra, a cobertura for adequada e o custo restante for viável. Se não, registrar a justificativa para encerrar em 60. Não abrir holdout para escolher o tamanho final.

## 8. Fase C — completar 120 (se aprovado no checkpoint)

1. Acrescentar as 48 novas instâncias de desenvolvimento restantes (4 por grupo).
2. Executar 48 × 4 variantes × 3 seeds = 576 novas execuções de desenvolvimento.
3. Acrescentar as 12 instâncias restantes de holdout (1 por grupo), mantendo 24 no split final.
4. Completar e validar 96 instâncias de desenvolvimento (1.152 runs) e 24 holdouts (288 runs).
5. Congelar metabasis_v2 com manifesto de split, hashes, commit, configuração, ambiente e proveniência.

Se a coleta de holdout for feita só após congelar modelos/critério, executar as 24 × 4 × 3 = 288 execuções do holdout em etapa isolada, sem disponibilizar os targets ao desenvolvimento até o protocolo estar congelado.

**Aceite final de coleta:** 120 instâncias inventariadas; 96 desenvolvimento; 24 holdout; 1.152 runs de desenvolvimento; 288 runs de holdout; 1.440 runs no total; zero chaves duplicadas ou ausentes.

## 9. Treino e avaliação

1. Usar apenas as 48 ou 96 instâncias de desenvolvimento para CV agrupada por instância.
2. Manter o LOO de 36 como diagnóstico histórico, não como evidência confirmatória.
3. Comparar aleatório, sempre Baseline, sempre Optuna, sempre Fuzzy, sempre Surrogate, melhor global do treino, RF classifier e RF regressor.
4. Fazer qualquer tuning, seleção de features, calibração ou escolha de modelo dentro do desenvolvimento; registrar o pipeline antes do holdout.
5. Congelar modelos, hiperparâmetros, seeds, baselines, métrica primária e código de avaliação.
6. Abrir o holdout uma única vez: 12 instâncias se encerrar em 60, ou 24 se completar 120.
7. Primária: regret por instância vs oráculo retrospectivo; comparar pareadamente com sempre Fuzzy. Reportar IC, média/mediana, vitórias/derrotas/empates, sensibilidade a rótulos low-confidence, métricas complementares e custo.

O holdout deve ser avaliado uma vez pelo pipeline congelado. Se houver alteração após observá-lo, esse conjunto deixa de ser confirmatório e será necessário um novo holdout independente para nova alegação confirmatória.

## 10. Comandos de referência já existentes

Estes comandos são válidos para inspeção/testes e para o runner atual, mas os comandos de produção v2 só devem ser fixados após o gate técnico da §4, porque o runner/freezer atuais têm metadados e defaults específicos do piloto.

~~~bash
# Estado do repositório
git status --short
git branch --show-current
git rev-parse HEAD

# Suíte relevante do piloto e dos componentes GWO
python -m pytest -q tests/test_meta_learning_features.py tests/test_meta_learning_metabasis_pilot.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py

# Extrator determinístico; output separado do freeze v1
python -m experiments.meta_learning.scripts.extract_instance_features --input-dir data/benchmarks/taillard --output results/meta_learning_metabasis_v2/inventory/instance_features_all.csv
~~~

Não execute o extrator acima até o inventário dos arquivos estar completo e validado; ele varre todos os ta*.txt sob o diretório informado.

Após o gate técnico, os comandos exatos de execução, agregação e freeze v2 deverão ser registrados aqui com os argumentos e paths validados. Não inventar nomes de scripts/flags antes de implementá-los.

## 11. Pacote a enviar após cada etapa

- Inventário e resumo por grupo; hashes e proveniência.
- Manifesto de split e SHA-256, com holdout identificado mas targets selados.
- Testes e saída completa, incluindo warnings/tracebacks.
- Manifesto de execução: commit, ambiente, configuração, seeds e timestamps.
- Relatório de completude: esperado/observado, missing, extra, duplicado, falhas e retentativas.
- Custos por grupo, variante, preparação Surrogate e execução.
- Artefatos agregados e freeze somente após auditoria.

## 12. Documentos relacionados

- [Decisão de expansão](../decisions/2026-11-27-meta-learning-expansion-v2.md)
- [Roadmap de conclusão](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [Status das fases](2026-11-27-meta-learning-phase-status.md)
- [LOO exploratório](2026-11-27-meta-learning-selector-loo-exploratory.md)
- [Reprodução A–D](2026-11-27-meta-learning-reproduction-ad.md)
- [Freeze imutável v1](../decisions/2026-11-27-metabasis-pilot-v1-freeze.md)
- [README Meta-Learning](../../experiments/meta_learning/README.md)
- [Inventário Taillard](../../data/benchmarks/taillard/README.md)
