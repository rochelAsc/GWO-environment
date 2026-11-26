# Auditoria técnica — diagnóstico inicial e atualização consolidada

- **Data:** 2026-11-22
- **Escopo:** inspeção estática de `scripts/sistemas_inteligentes_entregavel.py`, `scripts/discrete_gwo_dpfsp.py`, `scripts/dpfsp_dd.py`, `scripts/run_gwo_pilot.py` e do protocolo vigente.
- **Status:** diagnóstico inicial; nenhuma correção do motor legado/Fuzzy/Surrogate foi aplicada nesta auditoria.
- **Regra:** resultados históricos permanecem preservados e não devem ser sobrescritos.

## 1. Higiene do repositório

Foi criado `.gitignore` para Python, pytest, ambientes virtuais, Jupyter, IDEs, arquivos de sistema e segredos locais. A regra não ignora `results/` globalmente, para não ocultar dados experimentais versionados intencionalmente.

A criação do `.gitignore` não remove arquivos já rastreados pelo Git. Foram encontrados cinco arquivos `.pyc` rastreados em `scripts/__pycache__/` e `tests/__pycache__/`; os cinco foram removidos do repositório em commits separados. Uma nova leitura da árvore Git confirmou que não restam diretórios `__pycache__` nem arquivos `.pyc` rastreados. Os arquivos locais do usuário não foram tocados.

## 2. Achados críticos no motor legado

### L-01 — fallback silencioso para instância sintética

`FlowShopEngine.carregar_instancia_txt` cria dados aleatórios quando o arquivo não existe e também quando ocorre qualquer exceção durante o parser. Isso pode fazer uma execução aparentemente válida avaliar uma instância sintética em vez do benchmark solicitado.

**Impacto:** invalida rastreabilidade e comparabilidade experimental.

**Status em 2026-11-22:** corrigido no caminho atualizado do notebook/export: ambos importam `scripts/legacy_pfs.py`, cujo loader falha com `FileNotFoundError` ou `ValueError` contextualizado. O módulo antigo embutido foi removido desses pontos de entrada.

### L-02 — contrato incorreto/ambíguo de métodos da classe

`carregar_instancia_txt` e `calcular_lower_bound_potts` são declarados no corpo de `FlowShopEngine` sem `self` nem `@staticmethod`. Chamadas via classe funcionam como funções não vinculadas, mas chamadas via instância falham por argumento adicional implícito.

**Impacto:** API frágil e erro de execução dependente da forma de chamada.

**Status em 2026-11-22:** corrigido no módulo atualizado: ambos os métodos são `@staticmethod`; testes cobrem chamada pela classe e pela instância.

### L-03 — parser legado não valida estrutura suficientemente

O parser assume posições fixas de linhas, não valida rigorosamente IDs de máquina, duplicatas, dimensões e quantidade de datas; qualquer erro cai no fallback sintético (L-01).

**Impacto:** arquivos malformados podem ser mascarados.

**Status em 2026-11-22:** parser estrito e testes de caracterização adicionados em `scripts/legacy_pfs.py` e `tests/test_legacy_pfs.py`. A gramática foi inferida das suposições do parser antigo; sem os arquivos PFS originais, a compatibilidade com todas as instâncias históricas continua não comprovada. Ver `docs/audits/2026-11-22-legacy-pfs-characterization.md`.

### L-04 — dinâmica do GWO legado é sequencial/in-place

A classe `GWO.optimize` atualiza cada lobo e os líderes imediatamente antes de atualizar o próximo lobo. Assim, lobos posteriores usam líderes que podem ter sido alterados durante a mesma iteração. A implementação random-key DPFSP-DD, por decisão documentada, usa fotografia congelada dos líderes e atualização síncrona.

**Impacto:** são dinâmicas diferentes; não podem ser apresentadas como a mesma implementação sem explicitar a distinção.

**Correção necessária:** preservar a versão histórica como referência caracterizada e decidir/documentar se o experimento PFS manterá a variante sequencial ou adotará uma variante síncrona nova. Não alterar silenciosamente.

### L-05 — orçamento legado não coincide com o protocolo

Com `max_iter=200`, a implementação avalia a população inicial e mais 200 populações atualizadas: `N * 201` chamadas (por exemplo, 6.030 para 30 lobos), enquanto o protocolo novo especifica 5.940 avaliações.

**Impacto:** comparação de orçamento desigual e divergência entre documentação e código.

**Correção necessária:** implementar parada por contador real de avaliações completas, explicitando o número de gerações por população. Não comparar resultados antigos como se tivessem orçamento 5.940.

### L-06 — decoder legado não representa DPFSP-DD

O `FlowShopEngine` modela uma sequência PFS compartilhada pelas máquinas (`sequences = [seq] * m`) ou sequências independentes por máquina no modo alternativo. Não modela atribuição de jobs a fábricas com sequências locais e due dates por job conforme o avaliador DPFSP-DD.

**Impacto:** o motor legado não pode ser usado como avaliador do DPFSP-DD.

**Correção necessária:** manter os motores separados e criar adaptadores/algoritmos específicos por família.

## 3. Achados no Optuna

### O-01 — sintonia compara custos diferentes

A função objetivo do Optuna varia `n_wolves` entre 10 e 60, mas mantém `max_iter=200`. Como cada iteração avalia toda a população, trials usam orçamentos de avaliações diferentes.

**Impacto:** a melhor configuração pode refletir maior número de avaliações, não melhor eficiência sob orçamento equivalente.

**Correção necessária:** sintonizar sob orçamento fixo de avaliações reais, com lotes completos ou regra de orçamento explicitamente justificada.

### O-02 — espaço de busca inclui schedules sem decisão metodológica

O estudo inclui `linear`, `exponential` e `sqrt`; a fórmula `exponential` implementada é quadrática, não exponencial. A API nova DPFSP-DD usa o nome correto `quadratic`.

**Impacto:** nomenclatura enganosa e busca com variantes não alinhadas à matriz de ablação congelada.

**Correção necessária:** preservar nomes históricos nos resultados antigos; em novas execuções usar fórmulas e nomes explicitamente documentados.

### O-03 — definição de Tunado não está vinculada a artefato de estudo reproduzível

O protocolo descreve GWO-55-Q como Tunado, mas o script legado cria um estudo Optuna com espaço variável e não há, no trecho auditado, carregamento/versionamento de um estudo que prove a seleção dessa configuração.

**Impacto:** não é possível rastrear a origem dos parâmetros fixos somente pelo código auditado.

**Correção necessária:** localizar o artefato histórico do estudo, registrar seus parâmetros/ambiente/objetivo e decidir se a sintonia será refeita sob orçamento justo.

## 4. Achados no Fuzzy

### F-01 — erro de variável no relatório

A execução atribui o resultado a `fuzzy`, mas o print seguinte referencia `best_fuzzy`, que não é definido nesse trecho.

**Impacto:** erro de execução ao alcançar essa linha.

### F-02 — controlador e algoritmo estão acoplados a estado global

O `ControlSystemSimulation` é global e compartilhado; a classe `GWO_Fuzzy` depende de variáveis globais `simulador` e `sistema_fuzzy`.

**Impacto:** dificulta isolamento entre execuções, testes, paralelismo e reprodutibilidade.

**Correção necessária:** encapsular controlador por instância de execução, com estado e histórico próprios.

### F-03 — sem contrato de orçamento equivalente

A implementação Fuzzy sobrescreve `optimize` e executa `max_iter` gerações completas, sem receber/validar `max_evaluations`. O número de avaliações é calculado implicitamente como `n_wolves * (max_iter + 1)`.

**Impacto:** não atende ao orçamento comparável do protocolo.

### F-04 — mantém dinâmica sequencial do legado

O Fuzzy atualiza posições e líderes lobo a lobo, herdando a dinâmica sequencial, enquanto o GWO random-key é síncrono.

**Impacto:** uma comparação Fuzzy vs GWO-55-Q pode confundir o efeito do controlador com o efeito da dinâmica de atualização.

**Correção necessária:** definir a variante-base do Fuzzy antes de comparar e manter todos os demais componentes iguais.

### F-05 — definição e escala das entradas precisam de justificativa

Diversidade é calculada pelo desvio padrão das coordenadas contínuas; estagnação conta gerações sem melhoria. As funções de pertinência e regras são heurísticas e não têm, no código auditado, validação de cobertura, análise de sensibilidade ou fundamentação registrada.

**Impacto:** o efeito do controlador não está cientificamente isolado nem justificado.

**Correção necessária:** documentar universo, normalização, regras, resolução de conflitos e testes de cobertura; comparar com GWO-55-Q sob mesmo orçamento.

## 5. Achados no Surrogate

### S-01 — vazamento entre treino e teste por permutações equivalentes

O código usa `train_test_split` nas linhas de chaves contínuas. Chaves diferentes podem decodificar para a mesma permutação; tais amostras podem cair simultaneamente em treino e teste.

**Impacto:** métricas de teste superestimam generalização para permutações não vistas.

**Correção necessária:** agrupar pelo identificador canônico da permutação decodificada antes da divisão, conforme já exige o protocolo.

### S-02 — modelo é treinado para uma única instância e reutilizado fora dela

A MLP é treinada com `inst_s = TESTE[0]` e seu vetor de entrada tem dimensão igual ao número de jobs dessa instância. A integração posterior usa a função global `fitness_surrogate` sem verificar identidade/dimensão da instância.

**Impacto:** não existe modelo válido e independente por instância; outras dimensões podem falhar e outras funções objetivo não são representadas.

**Correção necessária:** treinar/validar um modelo por instância e armazenar metadados, dimensão, scaler e identidade do benchmark.

### S-03 — busca Surrogate reporta previsão, não qualidade real

O GWO otimizado pelo modelo retorna `best_surr`, que é uma previsão da MLP. O código não decodifica e reavalia a solução final no motor real nessa comparação.

**Impacto:** o resultado não mede a qualidade da solução encontrada pelo Surrogate e pode premiar erro de predição.

**Correção necessária:** decodificar a melhor solução e reavaliá-la no avaliador real; registrar previsão e valor real separadamente.

### S-04 — custo de treino e orçamento de consultas não são contabilizados de modo comparável

O código mede tempos em um teste separado e usa `max_iter=100` para comparar GWO real e Surrogate, sem contabilização integrada do orçamento de treinamento, consultas ao modelo e avaliação final.

**Impacto:** speedup e qualidade não são comparáveis ao protocolo principal.

**Correção necessária:** instrumentar treino, inferência, avaliações reais de treino/validação e consultas Surrogate em contadores distintos.

### S-05 — amostras LHS não equivalem a permutações únicas

O conjunto LHS é amostrado em espaço contínuo e avaliado após `argsort`; muitas chaves distintas podem decodificar para a mesma permutação.

**Impacto:** 500 amostras não garantem 500 exemplos combinatórios distintos.

**Correção necessária:** registrar total de amostras e permutações únicas; medir cobertura e adequar a validação ao número de grupos disponíveis.

## 6. Execução e organização do legado

O arquivo `scripts/sistemas_inteligentes_entregavel.py` é um script exportado de notebook, contém comandos mágicos `!pip`, imports de `google.colab.files`, uploads/downloads interativos e execução de experimentos no escopo global.

**Impacto:** não é um módulo importável/CLI local confiável e não permite testes unitários isolados.

**Correção necessária:** preservar esse arquivo como registro histórico; extrair código necessário para módulos sem efeitos colaterais, dependências Colab opcionais e comandos explícitos.

## 7. Sequência recomendada após esta auditoria

1. **Concluído:** inventariar e remover os arquivos `__pycache__` rastreados.
2. **Parcialmente concluído:** parser/avaliador caracterizados com fixtures sintéticas e fallback removido do notebook/export atualizado. Falta executar a suíte no ambiente local e validar o parser contra instâncias PFS históricas reais, se forem recuperadas.
3. **Proveniência parcialmente delimitada:** o responsável confirmou que o material já mapeado é todo o conteúdo utilizado e que não houve outro dataset/conteúdo. O ZIP DPFSP-DD está identificado e auditado; o subconjunto exato de instâncias PFS dos experimentos antigos não foi recuperado. Não afirmar que as 23 instâncias antigas são Taillard sem evidência. Ver `docs/audits/2026-11-22-dataset-provenance.md`.
4. Congelar uma matriz de aplicabilidade por família. O GWO random-key DPFSP-DD não substitui automaticamente o GWO PFS histórico.
5. Auditar e refazer Optuna sob orçamento comparável, se a sintonia fizer parte dos resultados novos.
6. Reimplementar Fuzzy com estado encapsulado e orçamento comum.
7. Reimplementar Surrogate com grupos por permutação e validação real final.
8. Só então criar runner integrado, piloto por família e bateria principal.

## 8. Limites desta auditoria

- Inspeção estática dos arquivos listados; nenhum benchmark legado foi executado nesta etapa.
- A existência de artefatos adicionais de Optuna, datasets Taillard ou código em notebooks ainda precisa ser verificada.
- Nenhum resultado histórico foi invalidado automaticamente; os achados indicam riscos/bugs que exigem rastrear quais execuções foram afetadas.


---

# Atualização consolidada — 25/11/2026

Esta seção atualiza o diagnóstico de 22/11/2026 à luz das correções, reconstruções experimentais, auditorias por semana e reprodução no Google Colab realizadas posteriormente. O conteúdo original foi preservado como registro do estado inicial; quando houver divergência entre uma recomendação antiga e esta atualização, prevalece o status mais recente descrito aqui.

## 9. Conclusão executiva atualizada

O repositório evoluiu de um conjunto heterogêneo de notebooks, código legado e resultados parcialmente documentados para um fluxo experimental modular, versionado e reproduzível para **PFSP com benchmarks Taillard**, com uma trilha documental separada para a mudança de escopo e para os experimentos históricos.

O estado atual permite considerar as etapas experimentais das Semanas 2 a 6 concluídas dentro dos escopos explicitamente documentados. A Semana 1 permanece como registro teórico/documental da proposta original de dengue/LSTM/GWO; não existe pipeline executável atual que reproduza esse experimento. A etapa de Meta-Learning foi retirada pelo professor e não integra os critérios de conclusão.

A conclusão não significa que todos os artefatos históricos foram validados retroativamente, nem que os resultados possam ser generalizados para qualquer instância de scheduling. As limitações de cobertura e as diferenças entre famílias de problemas permanecem relevantes.

## 10. Atualização dos achados iniciais

### 10.1 Motor legado e separação entre famílias

- Os caminhos experimentais atuais mantêm separados o PFS/PFSP de makespan e o DPFSP-DD. O motor legado não é tratado como avaliador substituto do DPFSP-DD.
- A reconstrução da Semana 2 implementa PFSP de uma fábrica, sem due dates, com makespan como objetivo e instâncias Taillard identificadas e versionadas.
- A representação random-key e o decoder por ordenação estável estão documentados nos scripts e protocolos da Semana 2.
- A correção da dinâmica congelada do GWO foi registrada em auditoria própria. A população agora recebe as novas posições a cada geração; testes de regressão cobrem a atualização da população e a variação da diversidade.
- Os resultados produzidos antes da correção foram preservados e não são tratados como evidência equivalente às execuções corrigidas. Semana 2 v2 e Semana 3 v2 foram reexecutadas após a correção.

### 10.2 Optuna — orçamento e rastreabilidade

A sintonia reconstruída da Semana 3 usa orçamento fixo de 15.030 avaliações exatas por execução, com população escolhida entre divisores do orçamento. Os seeds de tuning (100–102) são separados dos seeds de avaliação final (0–29). Os parâmetros selecionados estão registrados em `results/week3_optuna_v2/best_params.json`.

A comparação final é feita em duas instâncias Taillard e não sustenta uma alegação geral de superioridade estatística do Optuna. Os resultados devem ser apresentados como evidência condicionada às instâncias e ao protocolo utilizados.

### 10.3 Fuzzy — reconstrução e limites

O controlador atual está separado em módulo próprio, com entradas, funções de pertinência, regras Mamdani, defuzzificação e integração com o GWO documentadas. A implementação corrigida possui rastreamento e testes.

A bateria completa da Semana 5 v2 contém 60 execuções (duas instâncias × 30 seeds), com 15.030 avaliações exatas por execução. As comparações pareadas com Baseline e Optuna não demonstraram superioridade estatística após os procedimentos definidos. Os resultados descritivos favoráveis em uma instância não devem ser convertidos em afirmação de vencedor universal.

O CSV histórico antigo de Fuzzy continua incompleto para reconstruir o controlador original; não foi usado para inferir regras ou preencher dados ausentes.

### 10.4 Surrogate — validação e custo

A Semana 4 v2 deduplica amostras pela permutação decodificada antes da separação treino/teste e treina modelos separados por instância. Os resultados publicados usam 2.000 permutações únicas por instância, com 1.600 amostras de treino e 400 de teste.

As métricas de teste permanecem moderadas, sobretudo na `ta011` (R² = 0,252; Spearman = 0,539). A inferência em lote apresenta speedup sobre avaliação exata, mas a inferência individual é mais lenta. O relatório de runtime documenta os pontos de equilíbrio e impede que a aceleração em lote seja apresentada como ganho universal.

Na Semana 6, a variante Surrogate prediz 30 candidatos por geração e reavalia exatamente os três melhores previstos. Apenas fitness exato atualiza líderes, arquivo elite e convergência. A bateria confirma 1.530 avaliações exatas e 15.000 predições por execução. O custo de preparação dos modelos (4.000 rótulos exatos) é reportado separadamente.

### 10.5 Semana 6 — benchmark integrado

A bateria publicada em `results/week6_benchmark_v1/` contém 240 execuções: quatro variantes, duas instâncias e 30 seeds. O total é de 2.797.200 avaliações exatas durante a busca, mais 4.000 rótulos exatos de preparação dos modelos, além de 900.000 predições Surrogate.

Resultados principais:
- `ta001`: Optuna apresentou a menor média (1268,40); Fuzzy teve menor desvio padrão (6,24); Surrogate foi o mais rápido, mas teve média 1275,13.
- `ta011`: Fuzzy apresentou a menor média (1633,83); Surrogate foi o mais rápido, mas teve média 1660,20.
- Friedman indicou diferenças globais entre variantes nas duas instâncias.
- Após correção de Holm, nenhuma comparação par a par foi significativa na `ta001`; na `ta011`, Surrogate foi significativamente pior que Baseline, Optuna e Fuzzy.

Os orçamentos de avaliações exatas não são iguais entre Surrogate e as demais variantes. A bateria compara estratégias conforme o protocolo, não algoritmos sob orçamento idêntico de avaliações exatas ou custo computacional total.

## 11. Reprodução independente no Google Colab

O notebook principal `notebooks/Sistemas_Inteligentes_Entregavel.ipynb` foi reconstruído como interface de reprodução dos scripts oficiais. O notebook histórico foi preservado separadamente.

A execução Colab `colab_20261125_01` foi publicada em `results/notebook_runs/colab_20261125_01/`, com manifesto que identifica commit, ambiente, hashes das instâncias, parâmetros e seeds. A auditoria dos artefatos verificou:

- 60 execuções da Semana 2;
- 30 trials Optuna e 60 avaliações finais da Semana 3;
- dois datasets/modelos e métricas da Semana 4;
- 60 execuções Fuzzy da Semana 5;
- 240 execuções da Semana 6;
- 180/180 correspondências de makespan entre Semana 2 e Baseline da Semana 6, Semana 3 e Optuna da Semana 6, e Semana 5 e Fuzzy da Semana 6;
- contadores de avaliações exatas e predições da Semana 6 coerentes com o protocolo.

A reprodução confirma consistência dos artefatos experimentais e resultados de qualidade nas etapas verificadas. **Não comprova integralmente a execução de todas as células nem a aprovação do pytest dentro daquela sessão Colab**, pois o ZIP não contém log completo de saída dessas células. Essa limitação está explicitada na auditoria específica.

As workflows de CI dos documentos de auditoria Colab e análise de runtime concluíram com sucesso:
- auditoria Colab: run 45742586029;
- análise de runtime: run 45742590733.

## 12. Tempos: interpretação entre ambientes

A análise de runtime compara a máquina local (Windows 11, Python 3.14.6) e o Colab (Linux, Python 3.13.18). Nas baterias comparadas, o Colab registrou tempos aproximadamente 1,7× a 2,1× maiores. Não há dados suficientemente detalhados e controlados de CPU, frequência, vCPU e carga concorrente para atribuir causalidade ou estabelecer fator universal de conversão.

Os tempos absolutos devem sempre vir acompanhados da identificação do ambiente. A diferença de runtime não invalida, por si só, a consistência dos makespans e contadores reproduzidos. O custo de treinamento do Surrogate permanece separado do custo de busca.

## 13. Matriz consolidada de situação por etapa

| Etapa | Situação atual | Evidência e ressalvas |
|---|---|---|
| Semana 1 — proposta original | Documental | Proposta original dengue/LSTM/GWO preservada; sem pipeline executável atual. |
| Semana 2 — GWO canônico PFSP | Concluída no escopo reconstruído | Duas instâncias Taillard, 30 seeds cada; versão corrigida reexecutada; protocolo e auditoria publicados. |
| Semana 3 — Optuna | Concluída no escopo reconstruído | Orçamento fixo, tuning/evaluation seeds separados; resultados finais e parâmetros versionados. |
| Semana 4 — Surrogate | Concluída no escopo reconstruído | Dataset deduplicado por permutação, modelos por instância, métricas e latência reportadas; generalização limitada. |
| Semana 5 — Fuzzy | Concluída no escopo reconstruído | Controlador documentado e bateria de 60 runs; sem evidência de superioridade estatística pós-hoc. |
| Semana 6 — benchmark | Concluída no escopo definido | 240 runs, estatística global e pós-hoc, custos separados e auditoria formal. |
| Semana 7 — Meta-Learning | Fora do escopo | Retirado pelo professor; não deve ser apresentado como entrega pendente. |
| Semana 8 — artigo e apresentação | Consolidação pendente | Exige sintetizar os resultados e limitações sem misturar famílias de problema ou resultados históricos. |

## 14. Limitações remanescentes e riscos de interpretação

1. **Cobertura pequena de benchmarks:** a bateria integrada usa apenas duas instâncias Taillard de 20 jobs. Não permite generalização ampla para outros tamanhos, distribuições ou variantes de scheduling.
2. **Mudança de escopo:** a proposta inicial era dengue/LSTM/GWO; o experimento consolidado é PFSP/Taillard. A transição precisa ser declarada, não retroativamente apagada.
3. **Histórico PFS tardiness:** os experimentos exploratórios antigos de PFS com due dates são distintos do PFSP/makespan reconstruído. Seus resultados não devem ser mesclados.
4. **Histórico DPFSP-DD:** o piloto DPFSP-DD é outra família de problema e não é continuação numérica da bateria PFSP/Taillard.
5. **Surrogate:** as métricas preditivas, em especial na `ta011`, limitam a qualidade do ranking e explicam o compromisso entre economia de avaliações e desempenho.
6. **Orçamento:** a comparação da Semana 6 não tem orçamento igual de avaliações exatas para Surrogate; os resultados devem ser apresentados como comparação de estratégias.
7. **Estatística:** os testes se restringem às duas instâncias e aos 30 blocos de seed por variante. Seeds iguais não garantem números aleatórios comuns idênticos.
8. **Runtime:** tempos dependem do ambiente; Colab e máquina local não devem ser agregados numa média única.
9. **Reprodução Colab:** os artefatos foram auditados, mas não há log integral que comprove cada saída de célula e o pytest naquela sessão.
10. **Semana 1:** não afirmar que dengue/LSTM foi executado no pipeline atual.
11. **Meta-Learning:** não o reintroduzir como requisito ou como etapa experimental concluída.

## 15. Recomendações atualizadas para a entrega

1. Usar PFSP/Taillard como núcleo experimental atual e explicar explicitamente a mudança de escopo em relação à proposta inicial.
2. Manter os relatórios históricos de PFS tardiness e DPFSP-DD em seções separadas, sem agregar métricas entre famílias.
3. Apresentar os resultados das Semanas 2–6 com seus protocolos, seeds, orçamentos, instâncias e ambiente.
4. Na Semana 6, declarar a diferença de avaliações exatas e o custo de preparação do Surrogate; não chamar a comparação de orçamento igual.
5. Reportar resultados de qualidade e tempos locais/Colab separadamente.
6. Não declarar superioridade geral de Optuna, Fuzzy ou Surrogate; descrever os resultados específicos por instância e testes pós-hoc.
7. Preservar resultados antigos e versões anteriores; qualquer experimento adicional deve receber novo identificador e protocolo.
8. Priorizar agora artigo e apresentação, incluindo limitações e evidências de reprodução. Não iniciar Meta-Learning como se fosse exigência do roteiro.

## 16. Documentos de referência desta atualização

- `docs/audits/2026-11-23-week1-theoretical-review.md`
- `docs/audits/2026-11-23-week2-reconstruction-status.md`
- `docs/audits/2026-11-23-week3-reconstruction-status.md`
- `docs/audits/2026-11-23-week4-corrected-pilot-status.md`
- `docs/audits/2026-11-23-week5-reconstruction-status.md`
- `docs/audits/2026-11-25-week5-fuzzy-v2-pilot-audit.md`
- `docs/audits/2026-11-25-week6-benchmark-audit.md`
- `docs/audits/2026-11-25-colab-reproduction-audit.md`
- `docs/reports/colab-vs-local-runtime-analysis.md`
- `docs/reports/week2_reconstruction_protocol.md`
- `docs/reports/week5_fuzzy_protocol.md`
- `docs/reports/week6_benchmark_protocol.md`
- `results/notebook_runs/colab_20261125_01/execution_manifest.json`

**Status final:** auditoria técnica inicial atualizada com o estado consolidado conhecido em 25/11/2026. A atualização não altera dados brutos, resultados históricos, protocolos experimentais ou conclusões estatísticas das auditorias específicas.
