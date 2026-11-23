# Auditoria técnica inicial — legado PFS, Fuzzy e Surrogate

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

**Correção necessária:** falhar explicitamente com `FileNotFoundError` ou erro de parsing contextualizado. Não manter fallback no caminho experimental.

### L-02 — contrato incorreto/ambíguo de métodos da classe

`carregar_instancia_txt` e `calcular_lower_bound_potts` são declarados no corpo de `FlowShopEngine` sem `self` nem `@staticmethod`. Chamadas via classe funcionam como funções não vinculadas, mas chamadas via instância falham por argumento adicional implícito.

**Impacto:** API frágil e erro de execução dependente da forma de chamada.

**Correção necessária:** declarar explicitamente como `@staticmethod` ou movê-los para funções de módulo, após mapear os consumidores.

### L-03 — parser legado não valida estrutura suficientemente

O parser assume posições fixas de linhas, não valida rigorosamente IDs de máquina, duplicatas, dimensões e quantidade de datas; qualquer erro cai no fallback sintético (L-01).

**Impacto:** arquivos malformados podem ser mascarados.

**Correção necessária:** caracterizar o formato PFS histórico e implementar parser estrito com testes. Não reutilizar automaticamente o parser DPFSP-DD, pois as famílias têm formatos diferentes.

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

1. Inventariar os arquivos rastreados `__pycache__` e removê-los do índice após a criação do `.gitignore`.
2. Criar testes de caracterização do parser, avaliador e dinâmica PFS legados; remover fallback sintético no caminho experimental.
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
