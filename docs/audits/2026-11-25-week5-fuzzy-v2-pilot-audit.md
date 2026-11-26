# Semana 5 — Auditoria do piloto Fuzzy v2

**Escopo:** auditoria estática e quantitativa dos artefatos publicados em `results/week5_fuzzy_pilot_v2/`. Nenhuma execução nova foi realizada nesta auditoria.

## 1. Integridade dos artefatos

Foram conferidos:
- `summary.json`
- `fuzzy_runs.csv`
- `fuzzy_convergence.csv`
- `fuzzy_trace.csv`
- implementações em `scripts/fuzzy_controller.py` e `scripts/gwo_pfs_fuzzy.py`
- protocolo em `docs/reports/week5_fuzzy_protocol.md`

Contagens observadas:
- 6 execuções: 2 instâncias × 3 seeds;
- 15.030 avaliações por execução;
- 3.000 linhas de trace: 500 gerações × 6 execuções;
- 1.002 linhas de convergência: 501 pontos × 2 instâncias;
- hashes das instâncias no summary correspondem aos identificadores usados no protocolo.

As comparações pareadas foram recalculadas diretamente cruzando instância e seed nos CSVs da Semana 2 v2 e Semana 3 v2. Os deltas coincidem com o summary.

## 2. Evolução da população e diversidade

O código substitui `positions` por `new_positions` ao final de cada geração. A diversidade é recalculada no início da geração seguinte a partir da população atualizada.

Em cada uma das seis execuções, a diversidade variou e diminuiu fortemente ao longo da execução. Intervalos observados:

| Execução | Diversidade inicial/máxima | Diversidade mínima |
|---|---:|---:|
| ta001 seed 0 | 0,330402 | 0,000946 |
| ta001 seed 1 | 0,330783 | 0,000978 |
| ta001 seed 2 | 0,337968 | 0,001496 |
| ta011 seed 0 | 0,330402 | 0,000891 |
| ta011 seed 1 | 0,330783 | 0,000874 |
| ta011 seed 2 | 0,337968 | 0,001006 |

Isso confirma que a diversidade não está congelada, mas revela convergência/colapso acentuado da população no espaço contínuo de random keys. A diversidade medida não equivale diretamente à diversidade de permutações.

## 3. Estagnação e resposta Fuzzy

A primeira geração com estagnação normalizada igual a 1 ocorreu em:
- ta001: seeds 0, 1 e 2 nas gerações 26, 55 e 38;
- ta011: seeds 0, 1 e 2 nas gerações 89, 37 e 38.

Última melhoria do melhor global:
- ta001: gerações 5, 65 e 165;
- ta011: gerações 298, 388 e 251.

Após atingir estagnação 1, o controlador não fica necessariamente constante porque a diversidade continua mudando. No piloto, o fator Fuzzy não atingiu o limite superior 1,5; a região de alta exploração observada fica próxima de 1,33 quando diversidade é baixa e estagnação é alta.

**Correção de interpretação:** não é correto dizer que o fator Fuzzy saturou no limite superior 1,5. O que satura é a entrada de estagnação em 1,0. Separadamente, o parâmetro `a` é limitado por clipping em 2,0: isso ocorreu em aproximadamente 14%–23% das gerações, dependendo da execução.

A combinação de diversidade muito baixa e estagnação máxima faz o controlador operar repetidamente na região de alta exploração. Isso é coerente com a base de regras atual, mas indica que o sinal de diversidade perde amplitude dinâmica ao longo da execução e que a janela de estagnação de 20 gerações é rapidamente saturada em algumas seeds.

## 4. Resultados e comparação pareada

| Instância | Fuzzy média | Desvio amostral | Baseline média | Tunado média |
|---|---:|---:|---:|---:|
| ta001 | 1269,67 | 8,08 | 1269,67 | 1265,00 |
| ta011 | 1626,00 | 0,00 | 1636,33 | 1647,67 |

Diferenças Fuzzy − referência por seed:

- ta001 vs baseline: +14, 0, −14; média 0.
- ta001 vs tunado: +14, 0, 0; média +4,67.
- ta011 vs baseline: −15, −8, −8; média −10,33.
- ta011 vs tunado: −51, −14, 0; média −21,67.

O resultado Fuzzy de ta011 foi 1626 nas três seeds. Isso é um empate entre os três valores finais, não evidência de determinismo do algoritmo ou de robustez. A amostra de três seeds é insuficiente para concluir superioridade. Os p-values de Wilcoxon calculados com n=3 são apenas descritivos e não sustentam inferência confiável.

## 5. Diagnóstico e decisão

1. O bug de população congelada foi corrigido no solver Fuzzy v2; a diversidade registrada comprova variação entre gerações.
2. O controlador recebe entradas dinâmicas, mas a estagnação satura cedo e a diversidade tende a valores muito baixos.
3. O piloto não revela falha de execução nem inconsistência de orçamento.
4. O desempenho é misto: empate médio com baseline em ta001, vantagem descritiva em ta011 e desvantagem média contra Optuna em ta001.
5. **Não ajustar regras, pertinências ou janela após observar apenas três seeds e depois tratar o mesmo piloto como validação independente.** Isso introduziria risco de ajuste ao conjunto de teste.
6. A recomendação é manter exatamente a configuração v2 congelada e executar a bateria confirmatória de 30 seeds, caso o custo seja aceitável. A bateria deve usar os mesmos seeds 0–29, instâncias e orçamento das versões comparadas. O piloto seeds 0–2 deve ser reconhecido como subconjunto exploratório e não como validação independente.
7. Antes da bateria, verificar se os CSVs baseline e tuned contêm os 30 seeds únicos por instância e se os parâmetros/versões estão identificados no metadata.

## 6. Limitações

A auditoria não prova generalização além de ta001 e ta011, nem superioridade estatística. Também não mede a diversidade discreta de permutações, nem avalia sensibilidade à janela de estagnação. Qualquer nova configuração de controlador deverá receber nova versão e novo conjunto de resultados, preservando esta v2.
