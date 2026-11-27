# Auditoria da distribuição de candidatos das variantes GWO

**Status:** instrumentação implementada; piloto local ainda não executado.  
**Escopo:** PFSP/Taillard, minimização de makespan, quatro variantes GWO da Semana 6.

## 1. Motivação

Os resultados da Semana 6 registram convergência, resultados finais e traces parciais do Fuzzy/Surrogate, mas não preservam as populações completas. O trace Surrogate contém somente os candidatos selecionados para reavaliação exata; o trace Fuzzy contém variáveis do controlador. Esses arquivos não permitem reconstruir a distribuição dos candidatos visitados.

O objetivo desta auditoria é coletar as populações completas geradas pelo Baseline, Optuna, Fuzzy e Surrogate, rotulá-las com makespan exato e estudar a distribuição efetivamente induzida pelas trajetórias GWO. Os rótulos diagnósticos nunca participam da busca.

## 2. Instrumentação não invasiva

As funções `gwo_pfs`, `gwo_pfs_fuzzy` e `gwo_pfs_surrogate` aceitam agora um callback opcional `population_observer(generation, positions)`.

- Geração `-1`: população inicial.
- Gerações `0..iterations-1`: populações candidatas após a atualização GWO.
- O callback recebe uma cópia defensiva da matriz random-key.
- O callback não é consultado para decidir líderes, fitness, seleção ou atualização.
- Sem callback, o caminho original permanece inalterado.

O runner `scripts/run_gwo_population_distribution_audit.py` calcula a permutação por stable argsort e o makespan exato de cada candidato dentro do callback. Esses cálculos são rótulos diagnósticos adicionais e não substituem nem alimentam a avaliação interna do algoritmo.

## 3. Piloto

Configuração padrão:

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

Cada variante gera 15.030 candidatos por seed, contando população inicial e populações de cada geração. Portanto, o piloto terá 75.150 candidatos por variante e 300.600 candidatos no total, antes de deduplicação analítica. O número de rótulos diagnósticos exatos será igual ao número de candidatos registrados.

Para Baseline, Optuna e Fuzzy, os rótulos diagnósticos duplicam o número de avaliações exatas já realizadas internamente. Para Surrogate, representam um custo adicional relevante, pois a busca normalmente avalia exatamente apenas os top-3 por geração. Esse custo será reportado separadamente e não deve ser confundido com o orçamento de busca da Semana 6.

## 4. Execução

A partir da raiz do repositório:

```bash
python -m pytest -q tests/test_gwo_population_observer.py
python -m experiments.meta_learning.scripts.run_gwo_population_distribution_audit
```

Para escolher seeds e diretório de saída:

```bash
python -m experiments.meta_learning.scripts.run_gwo_population_distribution_audit \
  --instance data/benchmarks/taillard/ta111.txt \
  --seeds 0 1 2 3 4 \
  --output results/gwo_population_distribution_audit_v1
```

O runner valida os hashes do surrogate e da configuração Optuna, grava populações por geração e marca uma execução como concluída somente após finalizar seu resultado. Se houver interrupção, execuções incompletas podem ser repetidas; as linhas de população são deduplicadas pela chave variante/instância/seed/geração/lobo ao concluir o conjunto configurado.

Artefatos:
- `populations.csv`: permutação, makespan exato, geração, lobo e contagem de permutações únicas na população;
- `runs.csv`: resultado e custos por execução;
- `metadata.json`: protocolo, seeds, hashes e versões do ambiente.

## 5. Validação da instrumentação

Os testes comparam execuções com e sem callback, usando as mesmas seeds, e verificam:
- makespan final idêntico;
- permutação final idêntica;
- curva de convergência idêntica;
- contadores de avaliações/previsões idênticos;
- callback chamado na população inicial e em todas as gerações;
- mutação deliberada da cópia recebida não altera o estado do otimizador.

O piloto ainda precisa ser executado no ambiente local. A aprovação dos testes automatizados não substitui a verificação de igualdade dos resultados de uma execução real.

## 6. Análise após o piloto

1. Integridade: número de candidatos por variante/seed, gerações ausentes, duplicatas e hashes.
2. Diversidade: frequência posicional, entropia por posição, precedência de pares e distância de Kendall.
3. Evolução temporal: métricas por geração e por faixas início/meio/fim.
4. Qualidade: distribuição do makespan, quantis e concentração dos melhores candidatos.
5. Comparação de variantes: diferença entre distribuições e taxas de repetição/convergência.

As análises devem considerar dependência temporal e agrupamento por execução. Candidatos de uma mesma trajetória não são observações estatisticamente independentes.

## 7. Próxima etapa de dados para modelos

O piloto de cinco seeds é apenas uma verificação de viabilidade, não um dataset de treino/teste. Se custo e integridade forem aceitáveis, coletar o conjunto completo de seeds 0–29 sob o mesmo protocolo. A divisão deverá ser feita por seed/execução, nunca por linha de candidato. Uma proposta inicial é seeds 0–19 para treino e 20–29 para teste, mantendo todas as variantes de uma seed no mesmo lado da divisão.

A avaliação do surrogate deve privilegiar ranking e recuperação de candidatos de baixo makespan (top-k recall, regret e precisão de seleção), além de RMSE/Spearman. O teste deverá representar trajetórias não vistas. Não selecionar modelos com base no holdout.

## 8. Limitações

- Uma única instância no piloto; não generalizar para outras dimensões PFSP.
- As populações de gerações consecutivas são correlacionadas.
- O piloto tem apenas cinco seeds e é exploratório.
- O custo diagnóstico de makespan exato não representa o custo normal da busca, principalmente para Surrogate.
- A distribuição observada depende das configurações congeladas e das seeds.
- Nenhuma alteração da dinâmica GWO ou conclusão sobre superioridade de variante está autorizada por esta auditoria.
