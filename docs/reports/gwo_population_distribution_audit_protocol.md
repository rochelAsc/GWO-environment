# Auditoria da distribuição de candidatos das variantes GWO

**Status:** piloto de cinco seeds executado; resumo publicado. A população completa permanece como artefato local não versionado (~551,40 MB).  
**Escopo:** PFSP/Taillard, minimização de makespan, quatro variantes GWO da Semana 6.

## 1. Motivação

Os resultados da Semana 6 registram convergência, resultados finais e traces parciais do Fuzzy/Surrogate, mas não preservam as populações completas. O trace Surrogate contém somente candidatos selecionados para reavaliação exata; o trace Fuzzy contém variáveis do controlador. Esses arquivos não permitem reconstruir a distribuição dos candidatos visitados.

O objetivo desta auditoria é coletar as populações completas geradas pelo Baseline, Optuna, Fuzzy e Surrogate, rotulá-las com makespan exato e estudar a distribuição efetivamente induzida pelas trajetórias GWO. Os rótulos diagnósticos nunca participam da busca.

## 2. Instrumentação não invasiva

As funções `gwo_pfs`, `gwo_pfs_fuzzy` e `gwo_pfs_surrogate` aceitam um callback opcional `population_observer(generation, positions)`.

- Geração `-1`: população inicial.
- Gerações `0..iterations-1`: populações candidatas após a atualização GWO.
- O callback recebe uma cópia defensiva da matriz random-key.
- O callback não é consultado para decidir líderes, fitness, seleção ou atualização.
- Sem callback, o caminho original permanece inalterado.

O runner `scripts/run_gwo_population_distribution_audit.py` calcula a permutação por stable argsort e o makespan exato de cada candidato dentro do callback. Esses cálculos são rótulos diagnósticos adicionais e não substituem nem alimentam a avaliação interna do algoritmo.

## 3. Configuração do piloto

| Parâmetro | Valor |
|---|---:|
| Instância | `ta111` (500 jobs × 20 máquinas) |
| Variantes | Baseline, Optuna, Fuzzy, Surrogate |
| Seeds | 0–4 |
| Baseline | 30 lobos × 500 iterações |
| Optuna | 45 lobos × 333 iterações |
| Fuzzy | 30 lobos × 500 iterações |
| Surrogate | 30 lobos × 500 iterações; top-3 |
| Instantes amostrados | População inicial + cada geração |
| Rótulo | Makespan exato |

Cada variante gera 15.030 candidatos por seed, contando população inicial e populações de cada geração. O piloto gera 75.150 candidatos por variante e 300.600 candidatos no total. O mesmo número de rótulos diagnósticos exatos foi calculado.

Para Baseline, Optuna e Fuzzy, os rótulos diagnósticos repetem cálculos exatos já realizados internamente. Para Surrogate, são avaliações diagnósticas adicionais, pois a busca avalia exatamente somente os candidatos selecionados pelo mecanismo top-k. Não confundir esse custo com o orçamento algorítmico da Semana 6.

**Identidade do modelo Surrogate:** o artefato original Week 4 para ta111 não estava disponível no caminho esperado. O piloto usou `results/meta_learning_cost_pilot_v2/surrogates/ta111`, cujo protocolo, SHA da instância e codificação foram verificados. Portanto, esta execução deve ser identificada como Surrogate com Cost Pilot v2, não como reprodução exata do modelo da Week 6. Hashes do modelo, instância e configuração Optuna constam em `metadata.json`.

## 4. Execução

A partir da raiz do repositório:

```bash
python -m pytest -q tests/test_gwo_population_observer.py
python -m scripts.run_gwo_population_distribution_audit
```

Para apontar explicitamente o modelo Cost Pilot v2:

```powershell
python -m scripts.run_gwo_population_distribution_audit `
  --surrogate-dir results/meta_learning_cost_pilot_v2/surrogates
```

Parâmetros adicionais podem ser consultados com:

```bash
python -m scripts.run_gwo_population_distribution_audit --help
```

O runner valida os hashes do surrogate e da configuração Optuna, grava populações por geração e marca uma execução como concluída somente após finalizar seu resultado. Se houver interrupção, execuções incompletas podem ser repetidas; as linhas de população são deduplicadas pela chave variante/instância/seed/geração/lobo ao concluir o conjunto configurado.

## 5. Resultados do piloto (26/11/2026)

O piloto foi concluído: 20 execuções (4 variantes × 5 seeds), 15.030 candidatos por execução e 300.600 rótulos diagnósticos.

| Variante | Makespan médio | Desvio-padrão amostral | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| Baseline | 28.479,4 | 332,7 | 28.042 | 28.845 |
| Optuna | 28.606,4 | 111,4 | 28.482 | 28.779 |
| Fuzzy | 28.449,4 | 334,0 | 28.103 | 28.874 |
| Surrogate | 28.494,6 | 110,6 | 28.317 | 28.610 |

Essas estatísticas são descritivas; cinco seeds não sustentam conclusão inferencial robusta. Os tempos medidos incluem instrumentação e rótulos diagnósticos, portanto não são diretamente comparáveis aos tempos originais da Semana 6.

Relatório completo: [2026-11-26-gwo-population-distribution-pilot.md](2026-11-26-gwo-population-distribution-pilot.md).

## 6. Artefatos

- `populations.csv`: permutação, makespan exato, geração, lobo e contagem de permutações únicas na população.
- `runs.csv`: resultado e custos por execução.
- `metadata.json`: protocolo, seeds, hashes e versões do ambiente.

Os arquivos `metadata.json` e `runs.csv` estão versionados em `results/gwo_population_distribution_audit_v1/`. O `populations.csv` tem aproximadamente 551,40 MB e foi excluído do Git para respeitar o limite de 100 MB por arquivo do GitHub. Ele deve ser preservado localmente e compartilhado por armazenamento externo antes da análise linha a linha. Não presumir que o arquivo esteja disponível no repositório remoto.

## 7. Validação da instrumentação

Os testes comparam execuções com e sem callback, usando as mesmas seeds, e verificam:
- makespan final idêntico;
- permutação final idêntica;
- curva de convergência idêntica;
- contadores de avaliações/previsões idênticos;
- callback chamado na população inicial e em todas as gerações;
- mutação deliberada da cópia recebida não altera o estado do otimizador.

Os três testes específicos do observador passaram localmente. A CI associada à publicação deve ser consultada separadamente; aprovação local não substitui o resultado do workflow.

## 8. Análise e próximos passos

A análise completa ainda depende do arquivo `populations.csv`. Antes de coletar 30 seeds:

1. preservar e disponibilizar o CSV por armazenamento externo;
2. validar contagem de linhas, gerações, indivíduos por população, duplicatas e consistência com `runs.csv`;
3. recalcular independentemente uma amostra de permutações e makespans;
4. revisar a deduplicação do runner para não carregar o CSV inteiro em memória;
5. produzir métricas de frequência posicional, entropia, precedência de pares, distância de Kendall, diversidade temporal e distribuição de makespan.

O piloto de cinco seeds é exploratório, não dataset final de treino/teste. Se a integridade e o custo forem aprovados, coletar seeds 0–29. Qualquer divisão para modelagem deverá ser feita por execução/seed, nunca por linha de candidato, pois observações de uma mesma trajetória são dependentes. Proposta inicial: seeds 0–19 para treino e 20–29 para teste, mantendo todas as variantes de uma seed no mesmo lado.

## 9. Limitações

- Uma única instância no piloto; não generalizar para outras dimensões PFSP.
- As populações de gerações consecutivas são correlacionadas.
- Cinco seeds são insuficientes para conclusões inferenciais fortes.
- O custo diagnóstico de makespan exato não representa o custo normal da busca, principalmente para Surrogate.
- A distribuição observada depende das configurações congeladas e das seeds.
- O Surrogate do piloto usa o Cost Pilot v2 para ta111, não o modelo original da Week 6.
- Nenhuma alteração da dinâmica GWO ou conclusão sobre superioridade de variante está autorizada por esta auditoria.
