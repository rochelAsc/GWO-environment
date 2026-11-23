# Semana 4 — Protocolo de reconstrução do Surrogate

## 1. Objetivo

Avaliar se uma rede neural pode aproximar o makespan do PFSP de Taillard com erro mensurável e custo computacional inferior ao avaliador exato. A reconstrução usa a mesma formulação, instâncias e ambiente experimental das Semanas 2 e 3. Ela não substitui nem mistura os resultados históricos de PFS com due dates/tardiness.

A pergunta central não é apenas se a rede ajusta os dados, mas se generaliza para permutações não vistas e se a inferência compensa o custo de gerar dados e treinar o modelo.

## 2. Escopo e dados

- Problema: PFSP de uma fábrica, sem due dates.
- Objetivo: minimizar makespan.
- Instâncias iniciais: `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas).
- Avaliador de referência: `scripts/pfs_taillard.py::makespan`.
- Decoder: `scripts/gwo_pfs.py::decode_random_keys`.
- Cada instância recebe um modelo independente. Não misturar alvos de instâncias com escalas e estruturas diferentes.

Amostras são geradas a partir de vetores de random keys por Latin Hypercube Sampling (LHS). Cada vetor é decodificado em uma permutação antes da construção das features. As features representam a posição/rank de cada job na permutação, normalizada para [0, 1]. Essa representação é invariante a transformações monotônicas das chaves e evita ensinar à rede diferenças numéricas entre vetores que codificam a mesma ordem.

Permutações repetidas devem ser identificadas e removidas antes da divisão dos dados. O protocolo registra quantidade bruta, quantidade única e taxa de duplicação.

## 3. Separação treino/teste e prevenção de vazamento

- Gerar conjuntos independentes por instância, com seed fixa.
- Usar somente o conjunto de treino para ajustar os pesos e qualquer transformação aprendida.
- Reservar um conjunto de teste independente, nunca usado para seleção de arquitetura ou early stopping.
- Dividir por permutação única, não por vetor de random keys bruto.
- Registrar seeds, hashes dos arquivos de instância e índices/identificadores das amostras.
- Reportar MSE, RMSE, MAE e R² no treino e no teste. O resultado principal é o teste.
- Fazer gráfico previsto versus real e resíduos no teste.

A primeira execução será um piloto para estimar o custo e a diversidade de permutações. O tamanho final do conjunto de treino será congelado somente após inspecionar o piloto; não aumentar a amostra sem registrar nova versão do protocolo.

## 4. Modelo inicial

Modelo de referência: `sklearn.neural_network.MLPRegressor`, com duas camadas ocultas de 64 neurônios, ativação ReLU, regularização L2 e seed fixa. Usar normalização das features e do alvo por pipeline, ajustada somente no treino. Early stopping, se habilitado, deve usar exclusivamente uma fração interna do conjunto de treino.

A arquitetura é um baseline reproduzível, não uma alegação de arquitetura ótima. A versão do scikit-learn, parâmetros completos, número de épocas, tempo de treinamento e estado de convergência devem ser registrados.

## 5. Avaliação de custo

Medir separadamente:
1. tempo para gerar amostras e obter rótulos exatos;
2. tempo de treinamento;
3. latência de inferência do surrogate, tanto por amostra quanto em lote;
4. latência do avaliador exato, nas mesmas permutações e com repetições suficientes para reduzir ruído de temporização;
5. custo total de preparação + treino + inferência.

Comparar tempos com a mesma máquina e o mesmo conjunto de permutações. Reportar mediana e dispersão, não apenas uma medição. Não chamar inferência isolada de speedup end-to-end: o custo de geração do dataset e treinamento precisa ser amortizado e explicitado.

O número de avaliações exatas usadas para construir o dataset deve ser contado como custo de treinamento do surrogate, separado das consultas preditivas.

## 6. Teste de seleção e falso ótimo

O erro preditivo médio não garante que a rede ordene corretamente soluções boas. Para verificar o risco de exploração de erro:
- selecionar, no conjunto de teste, as permutações com menores makespans previstos;
- reavaliar exatamente essas permutações;
- comparar ranking previsto e ranking real, além do erro dos melhores candidatos;
- registrar o melhor valor previsto e seu makespan exato.

Uma previsão não será reportada como fitness obtido. Toda solução escolhida pelo surrogate deve ser reavaliada pelo avaliador exato antes de ser comparada à baseline.

## 7. Critérios de conclusão

A etapa só será considerada validada quando houver:
- dataset rastreável por instância e seed;
- divisão sem sobreposição de permutações entre treino e teste;
- métricas de regressão no teste;
- gráficos previsto versus real e resíduos;
- tempos de geração, treino, inferência e avaliação exata;
- avaliação exata dos candidatos selecionados pelo modelo;
- testes automatizados para decoder/features, separação dos dados, métricas e reprodutibilidade;
- auditoria com limitações explícitas.

Não é requisito que o surrogate seja mais rápido ou mais preciso que o avaliador exato. Um resultado negativo é válido e deve ser reportado. Em instâncias pequenas, o custo da rede pode superar o custo do cálculo exato.

## 8. Artefatos previstos

- `scripts/surrogate_pfs.py`: features, geração de amostras, treino e métricas.
- `scripts/run_week4_surrogate.py`: execução reproduzível por instância e geração de artefatos.
- `tests/test_week4_surrogate.py`: testes unitários e de reprodutibilidade.
- `docs/reports/week4_surrogate_protocol.md`: este protocolo.
- `results/week4_surrogate_v1/`: dados, modelo serializado, métricas, tempos, metadados e gráficos.
- `docs/audits/2026-11-23-week4-reconstruction-status.md`: auditoria final.

Os arquivos históricos em `data/experimental/` permanecem imutáveis e não são usados como evidência de desempenho nesta reconstrução.
