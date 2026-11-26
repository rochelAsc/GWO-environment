# Protocolo v2 — correção do LHS e auditoria de distribuição

**Data:** 26/11/2026  
**Status:** implementação versionada; resultados experimentais ainda não executados.

## Objetivo

Corrigir a limitação identificada na curva v1: o gerador anterior concatenava blocos de até 512 pontos, o que não constitui um único Latin Hypercube de tamanho N. A v1 e seus resultados permanecem imutáveis e devem continuar descritos como LHS em blocos.

## LHS global

O runner v2 cria, para cada tamanho e repetição, um único objeto `scipy.stats.qmc.LatinHypercube` e solicita exatamente N pontos em uma chamada. Os vetores de random keys são decodificados por `argsort` estável.

Se duas ou mais linhas decodificarem para a mesma permutação, o design completo é descartado. Uma nova tentativa gera um novo design global com uma seed filha determinística derivada da seed principal e do índice da tentativa. Designs nunca são concatenados. O número de tentativas é registrado; se o limite for excedido, a execução falha explicitamente em vez de produzir um conjunto que viole o protocolo.

A propriedade Latin é testada verificando que cada dimensão contém exatamente uma amostra em cada estrato de tamanho 1/N.

## Diagnósticos persistidos

Cada linha de execução registra:
- quantidade de permutações únicas e duplicadas;
- SHA-256 da matriz ordenada de permutações;
- desvio máximo das frequências job × posição em relação à frequência uniforme;
- entropia média normalizada das posições dos jobs;
- desvio médio e máximo das frequências de precedência entre pares em relação a 0,5;
- tamanho da subamostra usada para precedência;
- distância de Kendall média, desvio e máximo em relação à primeira permutação da subamostra;
- tentativas completas do LHS e versões de Python, NumPy, SciPy e scikit-learn.

As frequências de posição usam o conjunto completo. As estatísticas de precedência e distância de Kendall usam uma subamostra determinística de até 512 permutações para limitar o custo O(m n²). Portanto, essas duas métricas são estimativas amostrais, não uma varredura de todos os pares do dataset.

Por padrão, as métricas resumidas e o hash são salvos no CSV. Use `--save-diagnostic-arrays` para salvar histogramas e matrizes de precedência em NPZ. Use `--save-permutations` para também persistir as permutações exatas em uint16; essa opção pode consumir espaço considerável.

## Execução

```bash
python -m pytest -q tests/test_meta_learning_learning_curve_v2.py
python -m experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 \
  --output results/meta_learning_surrogate_learning_curve_v2
```

Para persistir as matrizes de diagnóstico e as permutações exatas:

```bash
python -m experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 \
  --save-diagnostic-arrays --save-permutations \
  --output results/meta_learning_surrogate_learning_curve_v2_full
```

A execução v2 não sobrescreve a pasta de resultados v1. A curva completa não deve ser iniciada até que os testes e o CI estejam aprovados.

## Limitações e interpretação

- A decodificação por argsort transforma o LHS contínuo em permutações discretas; a propriedade Latin aplica-se às random keys, não implica uniformidade das permutações.
- Rejeitar um design inteiro quando há colisões preserva a integridade do design aceito, mas condiciona a distribuição dos designs aceitos à ausência de colisões. O número de tentativas deve ser reportado.
- Frequências de posição próximas de 1/n e precedência próxima de 0,5 são diagnósticos, não prova de uniformidade conjunta no espaço de n! permutações.
- A população produzida pelo GWO não está incluída nesta etapa; sua coleta e comparação constituem a etapa seguinte.
- Nenhum resultado da curva v1 é recalculado ou substituído por esta correção.
