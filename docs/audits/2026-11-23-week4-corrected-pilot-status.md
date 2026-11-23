# Auditoria da Semana 4 — piloto corrigido (v2)

**Status:** implementação corrigida e CI aprovada; execução experimental v2 pendente.

## 1. Preservação do histórico

O piloto original em `results/week4_surrogate_pilot/` permanece inalterado. Ele não é sobrescrito nem reinterpretado como resultado da versão corrigida.

A execução v1 registrou 300 permutações únicas por instância:
- `ta001`: RMSE de teste 49,68; R² 0,523; Spearman 0,734.
- `ta011`: RMSE de teste 78,31; R² -0,015; Spearman 0,224.

Esses resultados mostram generalização fraca em `ta011`. Os tempos v1 não devem ser usados como comparação definitiva, pois os caminhos de medição não partiam diretamente dos mesmos vetores brutos de random keys.

## 2. Correção metodológica implementada

A versão v2 de `scripts/run_week4_surrogate.py`:
- preserva os vetores LHS originais de random keys;
- deduplica por permutação decodificada, mantendo uma chave representativa por permutação;
- gera features por stable argsort seguido de codificação de posições normalizadas;
- mede o avaliador exato e o surrogate sobre os mesmos vetores de random keys do conjunto de teste;
- inclui a decodificação nos dois caminhos e a codificação de features/inferência no caminho surrogate;
- faz aquecimento e 30 repetições, reportando mediana, média, desvio padrão, mínimo e máximo;
- calcula speedup de inferência em lote e individual em relação ao avaliador exato;
- grava as random keys e as features no dataset CSV para rastreabilidade.

A comparação continua sendo microbenchmark de avaliação, não speedup end-to-end do GWO. Geração do dataset e treinamento permanecem custos separados.

## 3. Testes e CI

Foram adicionados testes para:
- codificação de permutação;
- conversão de random keys em features;
- rejeição de chaves/permutação inválidas;
- reprodutibilidade do LHS e deduplicação;
- correspondência entre chaves brutas e features;
- métricas de regressão.

A execução GitHub Actions do commit `30a847c` concluiu com sucesso: 91 testes aprovados. A compilação convencional também foi aprovada.

## 4. Execução pendente

Comando do piloto corrigido:

```bash
python -m scripts.run_week4_surrogate --samples 300 --output results/week4_surrogate_pilot_v2
```

Após publicar `results/week4_surrogate_pilot_v2/`, revisar:
- métricas de teste, principalmente R² e Spearman;
- dispersão das latências nas 30 repetições;
- speedup em lote e individual;
- custo de geração dos rótulos e treinamento;
- comportamento dos dez candidatos selecionados pelo menor fitness previsto.

A expansão para 2.000 amostras permanece condicionada à inspeção dos artefatos v2:

```bash
python -m scripts.run_week4_surrogate --samples 2000 --output results/week4_surrogate_v2
```

Não afirmar que o surrogate é mais rápido ou que generaliza adequadamente antes de analisar esses resultados.

## 5. Limitações

- O teste é uma divisão aleatória de permutações amostradas por LHS; não demonstra generalização para todo o espaço de permutações.
- O speedup de inferência não inclui o custo de construir o dataset e treinar a rede.
- A seleção dos melhores candidatos é avaliada dentro do conjunto de teste e deve ser interpretada como diagnóstico de ranking, não como avaliação independente de uma busca GWO integrada.
- A execução v2 ainda não foi realizada nesta auditoria.
