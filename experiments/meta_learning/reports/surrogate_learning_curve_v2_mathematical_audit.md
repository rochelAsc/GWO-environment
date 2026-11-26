# Auditoria matemática da curva de aprendizagem v2 — 26/11/2026

## 1. Escopo e integridade

Fonte: `results/meta_learning_surrogate_learning_curve_v2_full/learning_curve_runs.csv`, commit `abddf993853270d198f8127555b05f02fad55310`.

- 100 execuções: 2 instâncias × 2 métodos × 5 tamanhos × 5 repetições.
- Instâncias: ta071 (100×10) e ta111 (500×20).
- Tamanhos: 300, 573, 1.095, 2.093 e 4.000.
- Teste externo fixo: 1.000 permutações por instância.
- O CI do commit foi verificado: job `pytest` concluído com sucesso (run `45855219651`).
- Os resultados completos, permutações e diagnósticos por execução foram publicados. LHS: 1 tentativa por desenho, sem duplicatas.

A análise usa a média das cinco repetições em cada ponto. A incerteza por ponto é apresentada como IC t de 95% (4 graus de liberdade). Com apenas cinco repetições, esses intervalos são necessariamente largos e sensíveis à distribuição dos resultados.

## 2. Definição matemática

A abscissa foi transformada para escala logarítmica:

\[
x=\log_2(N)
\]

Assim, uma unidade em x representa aproximadamente dobrar o número de amostras. Para uma métrica média \(\bar y_i\), a inclinação discreta entre pontos consecutivos é:

\[
g_i=\frac{\bar y_{i+1}-\bar y_i}{x_{i+1}-x_i}
\]

A curvatura discreta foi estimada pela diferença entre inclinações adjacentes:

\[
c_i=\frac{2(g_{i+1}-g_i)}{x_{i+2}-x_i}
\]

Interpretação:
- RMSE: inclinação negativa indica redução do erro por duplicação aproximada de N.
- Spearman/Kendall/R²: inclinação positiva indica melhora.
- Curvatura positiva/negativa indica mudança local na taxa de ganho, não prova isoladamente uma inflexão de uma função contínua.

Os intervalos de confiança dos pontos não foram convertidos em testes de significância das inclinações. As amostras LHS são desenhos independentes entre tamanhos; no braço uniforme, os conjuntos são prefixos aninhados. Além disso, as seeds do modelo mudam com N. Portanto, parear artificialmente a repetição 1 de N com a repetição 1 de outro N não produz um desenho pareado válido. As inclinações e curvaturas abaixo são descrições das médias observadas, não testes confirmatórios.

## 3. Resultados — pontos observados

### ta071 (100 jobs × 10 máquinas)

| Método | N | RMSE média [IC95%] | Spearman média [IC95%] |
|---|---:|---:|---:|
| LHS | 300 | 161,12 [156,12; 166,11] | 0,159 [0,093; 0,224] |
| LHS | 573 | 154,17 [149,94; 158,40] | 0,194 [0,121; 0,266] |
| LHS | 1.095 | 147,90 [146,42; 149,39] | 0,296 [0,273; 0,320] |
| LHS | 2.093 | 144,51 [142,92; 146,10] | 0,341 [0,309; 0,374] |
| LHS | 4.000 | 139,83 [137,70; 141,96] | 0,404 [0,386; 0,423] |
| Uniforme | 300 | 160,73 [156,89; 164,58] | 0,175 [0,113; 0,237] |
| Uniforme | 573 | 153,16 [150,34; 155,98] | 0,247 [0,189; 0,304] |
| Uniforme | 1.095 | 147,59 [143,26; 151,93] | 0,292 [0,239; 0,345] |
| Uniforme | 2.093 | 145,19 [142,95; 147,44] | 0,331 [0,311; 0,352] |
| Uniforme | 4.000 | 139,82 [138,22; 141,43] | 0,398 [0,382; 0,414] |

### ta111 (500 jobs × 20 máquinas)

| Método | N | RMSE média [IC95%] | Spearman média [IC95%] |
|---|---:|---:|---:|
| LHS | 300 | 386,78 [373,69; 399,87] | 0,051 [0,014; 0,089] |
| LHS | 573 | 376,67 [367,36; 385,97] | 0,044 [0,004; 0,084] |
| LHS | 1.095 | 360,70 [350,66; 370,73] | 0,081 [0,046; 0,116] |
| LHS | 2.093 | 350,83 [345,68; 355,99] | 0,112 [0,079; 0,146] |
| LHS | 4.000 | 340,82 [338,99; 342,64] | 0,151 [0,127; 0,175] |
| Uniforme | 300 | 381,77 [359,16; 404,37] | 0,046 [0,027; 0,064] |
| Uniforme | 573 | 379,35 [368,95; 389,76] | 0,016 [-0,025; 0,057] |
| Uniforme | 1.095 | 366,17 [359,26; 373,08] | 0,055 [0,033; 0,078] |
| Uniforme | 2.093 | 352,65 [343,02; 362,28] | 0,109 [0,035; 0,183] |
| Uniforme | 4.000 | 343,03 [338,71; 347,35] | 0,138 [0,096; 0,179] |

## 4. Inclinações discretas por intervalo

Unidade: variação da métrica por duplicação aproximada de N (uma unidade de \(\log_2 N\)). Os valores são calculados a partir das médias.

### RMSE

| Instância | Método | 300→573 | 573→1.095 | 1.095→2.093 | 2.093→4.000 |
|---|---|---:|---:|---:|---:|
| ta071 | LHS | -7,44 | -6,71 | -3,63 | -5,00 |
| ta071 | Uniforme | -8,11 | -5,96 | -2,57 | -5,75 |
| ta111 | LHS | -10,83 | -17,09 | -10,55 | -10,72 |
| ta111 | Uniforme | -2,59 | -14,11 | -14,46 | -10,29 |

### Spearman

| Instância | Método | 300→573 | 573→1.095 | 1.095→2.093 | 2.093→4.000 |
|---|---|---:|---:|---:|---:|
| ta071 | LHS | +0,037 | +0,110 | +0,048 | +0,067 |
| ta071 | Uniforme | +0,077 | +0,048 | +0,042 | +0,071 |
| ta111 | LHS | -0,008 | +0,039 | +0,034 | +0,041 |
| ta111 | Uniforme | -0,031 | +0,042 | +0,057 | +0,031 |

### Curvatura discreta

Valores de RMSE:

| Instância | Método | Centro 573 | Centro 1.095 | Centro 2.093 |
|---|---|---:|---:|---:|
| ta071 | LHS | +0,781 | +3,294 | -1,468 |
| ta071 | Uniforme | +2,310 | +3,626 | -3,404 |
| ta111 | LHS | -6,702 | +7,002 | -0,180 |
| ta111 | Uniforme | -12,336 | -0,378 | +4,462 |

Valores de Spearman:

| Instância | Método | Centro 573 | Centro 1.095 | Centro 2.093 |
|---|---|---:|---:|---:|
| ta071 | LHS | +0,078 | -0,066 | +0,020 |
| ta071 | Uniforme | -0,030 | -0,006 | +0,031 |
| ta111 | LHS | +0,051 | -0,006 | +0,008 |
| ta111 | Uniforme | +0,078 | +0,017 | -0,028 |

## 5. Interpretação crítica

### 5.1 RMSE

- As médias de RMSE caem em todos os intervalos, nas duas instâncias e nos dois métodos. Não há reversão da tendência global no intervalo observado.
- Em ta071, o ganho marginal diminui de forma clara até N=2.093; o intervalo final volta a apresentar inclinação mais negativa. Isso é compatível com oscilação na taxa de ganho, não com saturação demonstrada.
- Em ta111, o LHS apresenta maior redução entre 573 e 1.095; o braço uniforme apresenta maior redução entre 573 e 2.093. A taxa volta a diminuir no último intervalo.
- Os sinais da curvatura mudam em alguns trechos. Com cinco pontos e cinco repetições, isso só permite apontar mudanças locais de concavidade aproximada; não é base suficiente para declarar pontos de inflexão estatisticamente estabelecidos.

### 5.2 Ordenação

- Spearman cresce de forma global em ta071 nos dois métodos, mas com incrementos desiguais.
- Em ta111, ambos os métodos têm uma queda inicial de Spearman entre 300 e 573, seguida de melhora consistente.
- Mesmo em N=4.000, Spearman médio é apenas 0,404/0,398 em ta071 e 0,151/0,138 em ta111 (LHS/uniforme). A ordenação aprendida continua fraca, principalmente na instância maior.
- Top-10 recall permanece muito baixo e instável. Não deve ser usado sozinho para inferir saturação: é uma métrica discreta, baseada em apenas dez posições e sensível a empates no makespan. A implementação atual usa `argsort` e não faz tratamento tie-aware; isso deve ser corrigido ou explicitamente limitado na análise consolidada.

### 5.3 Variabilidade

Os ICs de RMSE e Spearman mostram variabilidade relevante em vários pontos, sobretudo ta111 e N pequeno. Em particular, o IC de RMSE uniforme de ta111 em N=300 é amplo. Cinco repetições são suficientes para diagnóstico exploratório, mas não para conclusões fortes sobre diferenças pequenas entre tamanhos ou métodos.

### 5.4 Distribuição das permutações

Os diagnósticos v2 indicam, em N=4.000, entropia de posição normalizada próxima de 1, desvio máximo marginal pequeno e desvio médio de precedência próximo de 0,017 para ambos os métodos/instâncias. Isso enfraquece a hipótese de um desequilíbrio marginal grosseiro na distribuição global. Não prova cobertura das regiões relevantes para makespan nem adequação da representação de entrada do MLP.

## 6. Resposta à hipótese de inflexões

Há mudanças de curvatura discreta nos quatro pares instância/método, mas elas não se alinham em um único N nem formam um padrão comum. Portanto:

1. Não há evidência suficiente para afirmar um ponto de inflexão estável.
2. Não há evidência de que a curva já tenha saturado em N=4.000.
3. A redução contínua do RMSE e a melhora global do ranking justificam estender a curva.
4. A baixa qualidade absoluta em ta111 justifica não interpretar a melhora como solução do problema de generalização.

## 7. Decisão para a extensão

Usar o gerador geométrico já implementado em `geometric_sample_sizes`, sem criar outra regra de progressão:

\[
\operatorname{geometric\_sample\_sizes}(8000,32000,3)=[8000,16000,32000]
\]

Manter:
- ta071 e ta111;
- LHS global por tamanho/repetição e braço uniforme;
- MLP 64×64 atual;
- 5 repetições;
- mesmo teste fixo de 1.000 permutações por instância (mesma seed-base);
- mesmos critérios, métricas e configurações de treinamento;
- arrays de diagnóstico e permutações completos;
- nova pasta de saída, sem sobrescrever v2_full.

A extensão acrescentará 60 ajustes de modelo e 1.120.000 avaliações exatas de makespan para rótulos de treino:

\[
2\text{ instâncias}\times2\text{ métodos}\times5\text{ repetições}\times(8000+16000+32000)=1.120.000
\]

O braço uniforme continuará usando prefixos aninhados de uma única amostra máxima por repetição. O LHS continuará gerando um desenho global independente para cada N/repetição, conforme a função v2.

Comando planejado:

```bash
python -m experiments.meta_learning.scripts.run_surrogate_learning_curve_v2 \
  --min-samples 8000 \
  --max-samples 32000 \
  --points 3 \
  --repeats 5 \
  --test-samples 1000 \
  --seed 20261128 \
  --save-diagnostic-arrays \
  --save-permutations \
  --output results/meta_learning_surrogate_learning_curve_v2_extension
```

Antes da bateria completa, executar uma repetição-piloto isolada com a mesma função/script e estimar tempo e armazenamento. Não usar a pasta final da bateria para o piloto.

## 8. Próximas etapas

1. Executar a extensão em N=8.000, 16.000 e 32.000.
2. Aplicar exatamente as mesmas definições de inclinação e curvatura à curva combinada (300–32.000), preservando a separação entre os dois métodos.
3. Auditar novamente incerteza, estabilidade, distribuição e empates do top-k.
4. Consolidar a análise da curva completa.
5. Só então comparar MLP, ExtraTrees/Random Forest e Gradient Boosting/HistGradientBoosting sobre os mesmos conjuntos, splits e seeds.

## 9. Limitações

- A curva é específica a duas instâncias Taillard; não permite generalizar a todas as instâncias PFSP.
- ICs t com cinco repetições são exploratórios.
- Inclinações e curvaturas finitas descrevem pontos discretos; não estimam uma função geradora conhecida.
- O teste uniforme fixo não mede diretamente a qualidade nas regiões visitadas pela trajetória do GWO.
- As métricas top-k atuais não tratam empates de makespan de forma explícita.
