# Semana 6 — Protocolo de benchmarking comparativo

**Status:** protocolo executado e auditado em 25/11/2026. Resultados: `../../results/week6_benchmark_v1/`. Auditoria: [2026-11-25-week6-benchmark-audit.md](../audits/2026-11-25-week6-benchmark-audit.md).

**Decisão associada:** [Benchmarking e Surrogate assistido](../decisions/2026-11-25-week6-surrogate-assisted-evaluation.md).

## 1. Objetivo e escopo

Comparar quatro variantes do GWO no PFSP clássico de uma fábrica, minimizando makespan, nas instâncias Taillard `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas):

1. Baseline;
2. Optuna;
3. Surrogate assistido;
4. Fuzzy.

Este experimento continua a mesma família PFSP/Taillard das Semanas 2–5. Não mistura PFS com tardiness nem DPFSP-DD. Os resultados de famílias distintas permanecem separados.

## 2. Implementações e configurações congeladas

| Variante | População | Iterações | Agenda/controle | Avaliações exatas por execução |
|---|---:|---:|---|---:|
| Baseline | 30 | 500 | Linear, a_start=2, a_end=0, expoente=1 | 15.030 |
| Optuna | 45 | 333 | a_start=1,5441; a_end=0,1082; expoente=0,5517 | 15.030 |
| Surrogate | 30 | 500 | MLP + reavaliação exata dos top 3 previstos/geração | 1.530 |
| Fuzzy | 30 | 500 | Mamdani da Semana 5 v2 | 15.030 |

A configuração Optuna é congelada com base em `results/week3_optuna_v2/best_params.json`; a configuração Fuzzy usa o controlador implementado em `scripts/gwo_pfs_fuzzy.py`. Não haverá nova sintonia nem ajuste de regras/pertinências durante a Semana 6.

Seeds: inteiros 0–29, comuns às quatro variantes e às duas instâncias. Total: 4 × 2 × 30 = **240 execuções**.

## 3. Política Surrogate

Para cada instância, carregar o modelo MLP treinado e serializado na Semana 4. Não usar o conjunto de teste para retreinar ou selecionar parâmetros. Registrar caminho e SHA-256 do modelo, além do hash da instância e das versões das bibliotecas.

Por execução:

1. Inicializar 30 vetores random-key com o seed correspondente e calcular o makespan exato de cada um.
2. Em cada geração, atualizar os 30 vetores com a dinâmica síncrona GWO e clipping em [0,1].
3. Decodificar e extrair as features dos 30 candidatos; executar uma previsão em lote.
4. Selecionar os três candidatos com menor previsão.
5. Reavaliar exatamente os três candidatos selecionados.
6. Atualizar o arquivo elite de três líderes apenas com soluções de fitness exato conhecido. A população completa avança para a geração seguinte.
7. Registrar a melhor solução exata e o makespan exato best-so-far. Previsões nunca aparecem como fitness final ou na curva de convergência.

Cada seleção consome três chamadas exatas mesmo quando há permutações duplicadas; registrar a quantidade de duplicatas como diagnóstico. O modelo permanece congelado durante toda a busca.

**Contadores por execução:** 30 avaliações exatas iniciais + 1.500 reavaliações = 1.530 avaliações exatas; 15.000 previsões; 500 lotes de inferência.

## 4. Orçamento agregado

| Variante | Execuções | Avaliações exatas/execução | Total de avaliações exatas |
|---|---:|---:|---:|
| Baseline | 60 | 15.030 | 901.800 |
| Optuna | 60 | 15.030 | 901.800 |
| Surrogate | 60 | 1.530 | 91.800 |
| Fuzzy | 60 | 15.030 | 901.800 |
| **Busca — total** | **240** | — | **2.797.200** |

Preparação do Surrogate: 2.000 avaliações exatas para rotular o dataset de cada instância, 4.000 no total, conforme os artefatos da Semana 4. Somando preparação e busca: **2.801.200 avaliações exatas**. A busca Surrogate também realiza 900.000 previsões (60 execuções × 15.000).

Os números são contadores de chamadas ao avaliador, não medidas de tempo. Tempo de geração de dados, treinamento, inferência e avaliação exata deve ser registrado separadamente.

## 5. Custo computacional

Para cada execução, registrar:
- tempo de parede total;
- tempo acumulado de avaliação exata;
- tempo acumulado de inferência, quando aplicável;
- número de avaliações exatas;
- número de previsões;
- número de lotes de inferência;
- número de candidatos duplicados entre os três selecionados;
- makespan final e permutação.

Para o Surrogate, registrar adicionalmente, por instância:
- tempo de geração dos dados e cálculo dos rótulos;
- tempo de treinamento;
- hash do arquivo `surrogate.joblib`;
- custo de preparação separado do custo da busca.

Apresentar três visões: tempo da busca sem preparação; custo de preparação; custo total (preparação + busca). Apresentar também custo amortizado por execução para 1, 10 e 30 execuções por instância, deixando explícitas as hipóteses. Não extrapolar o speedup de microbenchmark da Semana 4 para o GWO completo.

## 6. Métricas de qualidade

Por variante e instância:
- média, mediana e desvio padrão amostral;
- mínimo e máximo;
- contagem de runs que alcançam o upper bound publicado;
- curva best-so-far média e desvio padrão por geração;
- resultados individuais por seed.

O upper bound publicado é referência de benchmark, não ótimo provado. Não chamar a diferença para UB de gap para ótimo conhecido.

## 7. Análise estatística

Executar separadamente para `ta001` e `ta011`:

1. Friedman para comparação global das quatro variantes, usando os 30 seeds como blocos.
2. Seis comparações pareadas bilaterais de Wilcoxon entre os pares de variantes.
3. Correção de Holm sobre as seis comparações dentro de cada instância.
4. Reportar p-values brutos e ajustados, diferenças pareadas, média e mediana das diferenças, e vitórias/empates/derrotas.

A análise não deve juntar as duas instâncias em uma amostra de 60 pares. Não afirmar superioridade estatística quando o resultado ajustado não sustentar essa conclusão. Reportar limitações do tamanho amostral e da cobertura de apenas duas instâncias.

## 8. Integridade, reprodutibilidade e artefatos

Diretório de saída novo: `results/week6_benchmark_v1/`. Não sobrescrever resultados das Semanas 2–5.

A execução deve produzir, no mínimo:
- CSV de resultados individuais;
- CSV de convergência por seed e agregado;
- CSV de tempos/contadores por execução;
- CSV de previsões e reavaliações Surrogate, ou log equivalente auditável;
- JSON de metadados com protocolo, parâmetros, seeds, ambiente, hashes das instâncias e modelos, timestamps e resumos;
- gráficos comparativos e curvas de convergência;
- relatório de análise estatística.

A gravação deve ser incremental e permitir detectar execuções ausentes sem duplicar linhas. O runner deve validar que cada combinação variante × instância × seed aparece exatamente uma vez e que os contadores correspondem ao protocolo.

## 9. Testes e critérios de aceitação

- [ ] Testes unitários do caminho Surrogate: top-3, reavaliação exata, arquivo de líderes exclusivamente exato, convergência exata e contadores.
- [ ] Testes de determinismo por seed e validação dos parâmetros.
- [ ] Testes de orçamento: 15.030 nas variantes exatas e 1.530 exatas + 15.000 previsões no Surrogate.
- [ ] Teste de que o modelo não é atualizado durante a busca.
- [ ] Testes de integração em uma instância e poucas seeds.
- [ ] Piloto curto executado e auditado antes da bateria completa.
- [ ] Bateria completa contém 240 execuções sem combinações faltantes ou duplicadas.
- [ ] Estatística, gráficos e resumos são gerados diretamente dos CSVs brutos.
- [ ] Testes automatizados e CI passam.

## 10. Limitações predefinidas

- Apenas duas instâncias Taillard; a conclusão é restrita a elas.
- O modelo Surrogate tem qualidade preditiva moderada, sobretudo em `ta011`.
- Reavaliar os três melhores previstos reduz, mas não elimina, o risco de erro de ranking.
- Orçamentos de avaliações exatas diferem entre Surrogate e variantes exatas; a comparação deve mostrar qualidade e custo, não alegar igualdade de orçamento.
- O custo de treino é pequeno, mas não gratuito; deve ser reportado e amortizado explicitamente.
- O protocolo não autoriza ajustes pós-hoc de modelo, regras Fuzzy ou parâmetros Optuna com base nos resultados finais.
