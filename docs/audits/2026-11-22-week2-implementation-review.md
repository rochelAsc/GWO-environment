# Revisão da Semana 2 — Implementação e validação do GWO baseline

- **Data:** 2026-11-22
- **Escopo:** implementação do GWO, modularidade, validação em benchmarks, parâmetros, convergência e repetibilidade.
- **Status:** implementação histórica localizada; aderência parcial ao roteiro. A validação exigida com benchmarks Taillard de PFS não está demonstrada pelos artefatos atualmente versionados.
- **Preservação:** revisão aditiva. Nenhum resultado, notebook ou código histórico foi sobrescrito.

## 1. Exigências do roteiro

A Semana 2 solicita:
1. implementação da versão canônica do algoritmo do zero, sem framework pronto para a lógica do solver;
2. avaliação em pelo menos duas instâncias/benchmarks Taillard para Permutation Flow Shop (PFS);
3. parâmetros padrão da literatura;
4. código-fonte modularizado e documentado;
5. histórico de convergência com média e desvio padrão de 30 execuções independentes.

A validação em funções contínuas genéricas pode ajudar a testar a mecânica matemática do GWO, mas não substitui os benchmarks Taillard de PFS especificados no roteiro.

## 2. Evidências localizadas

### 2.1 GWO contínuo histórico

A classe `GWO` está embutida em `scripts/sistemas_inteligentes_entregavel.py`, export do notebook Colab. O código implementa:
- inicialização aleatória da população dentro dos limites;
- identificação de alpha, beta e delta;
- coeficientes `A` e `C` e três estimativas de posição por dimensão;
- média das três estimativas, clipping nos limites e avaliação da função objetivo;
- contador de avaliações e histórico do melhor fitness;
- gerador aleatório local com seed.

A lógica foi escrita diretamente com NumPy, sem delegar a atualização do GWO a uma biblioteca de otimização. Isso constitui evidência de implementação própria da mecânica básica.

### 2.2 Benchmarks contínuos incluídos

O mesmo export define três funções contínuas:
- Rastrigin;
- Rosenbrock;
- Ackley.

O bloco experimental configura 30 execuções com seeds 0–29, 30 lobos e 500 iterações por função, calcula média e desvio padrão do histórico e prepara um gráfico. Portanto, há código para três testes contínuos e para a agregação de 30 execuções.

**Limite de evidência:** o código-fonte demonstra a configuração pretendida, mas os artefatos atualmente localizados não fornecem uma tabela bruta versionada por seed nem um gráfico final rastreável que permita confirmar, independentemente, que as 90 execuções foram concluídas com sucesso e produziram os valores apresentados. A presença do loop não prova a execução integral.

### 2.3 Implementações posteriores

O repositório contém também:
- `scripts/legacy_pfs.py`: motor/parser PFS de uma fábrica, separado do export histórico; não contém a classe GWO;
- `scripts/discrete_gwo_dpfsp.py`: solver random-key para DPFSP-DD, modular e testado;
- `scripts/dpfsp_dd.py`: parser e avaliador independente para DPFSP-DD;
- testes de caracterização do GWO histórico e testes do solver/parser DPFSP-DD.

O solver DPFSP-DD é uma implementação posterior e distinta. Sua codificação de 2n chaves, atualização síncrona, líderes congelados por geração e arquivo elitista não devem ser descritos como se fossem a mesma implementação do GWO contínuo histórico.

## 3. Divergências técnicas relevantes

### 3.1 A implementação histórica não atualiza uma geração de forma síncrona

No GWO histórico, cada lobo é atualizado e avaliado imediatamente; a hierarquia alpha/beta/delta também é alterada imediatamente. Assim, os lobos seguintes podem usar líderes promovidos durante a mesma geração. Isso caracteriza uma atualização sequencial/in-place, diferente da dinâmica síncrona usual em que todos os lobos usam o mesmo conjunto de líderes congelado durante a geração.

Os testes de caracterização em `tests/test_legacy_gwo_characterization.py` registram esse comportamento com uma sequência de avaliação de referência. Portanto, não é uma hipótese: é uma propriedade observada e testada do código histórico.

### 3.2 Agenda do parâmetro a

A implementação calcula:
- linear: `a = 2 - 2(t/T)`;
- modo chamado `exponential`: `a = 2(1 - (t/T)^2)`, que é quadrático;
- raiz: `a = 2 sqrt(1 - t/T)`.

O loop executa `t = 0, ..., T-1`; logo, o valor zero em `t=T` não é usado numa atualização. O último valor efetivamente usado é positivo. O nome histórico `exponential` deve ser preservado nos dados antigos, mas novas execuções devem chamar essa curva de `quadratic`.

### 3.3 Orçamento de avaliações

A população inicial é avaliada antes das iterações. Com `N` lobos e `T` iterações, o custo é `N(T+1)` avaliações. Os testes automatizados verificam essa contagem e o comprimento `T+1` do histórico. Comparações devem usar o contador real, não apenas o número de iterações.

### 3.4 Modularidade

A classe GWO histórica está dentro de um export de notebook que contém magics e comandos específicos do Colab; o próprio README alerta que esse export não é um módulo Python convencional. O motor PFS foi separado, mas o solver histórico ainda não está isolado em um módulo importável e reutilizável. Assim, o requisito de código-fonte modularizado está apenas parcialmente atendido.

## 4. A lacuna dos benchmarks Taillard

O roteiro especifica benchmarks Taillard para PFS. O conjunto `data/instances/DPFSP_DD.zip` é DPFSP com due dates, isto é, problema distribuído com atribuição de jobs a fábricas e objetivo Total Tardiness. Ele não é intercambiável com instâncias Taillard de PFS de uma fábrica.

O motor `scripts/legacy_pfs.py` representa PFS de uma fábrica e aplica uma permutação comum às máquinas. O parser do DPFSP-DD e seu solver tratam a atribuição às fábricas separadamente. As duas famílias devem permanecer isoladas.

Na árvore atual do repositório não foram localizados arquivos de instâncias Taillard de PFS usados na validação da Semana 2. O README também registra que as instâncias PFS exatas dos experimentos históricos não foram recuperadas. Consequentemente:
- Rastrigin, Rosenbrock e Ackley não satisfazem, sozinhas, a exigência específica de Taillard/PFS;
- o ZIP DPFSP-DD não deve ser rotulado como Taillard/PFS;
- resultados do PFS histórico e do DPFSP-DD não podem ser agregados como se fossem o mesmo problema.

## 5. Checklist da Semana 2

| Exigência | Evidência | Situação |
|---|---|---|
| GWO implementado do zero | Classe própria com equações, coeficientes, líderes e atualização em NumPy | Parcialmente atendido; dinâmica sequencial difere da atualização canônica síncrona |
| Pelo menos dois benchmarks Taillard para PFS | Nenhuma instância Taillard de PFS foi localizada no conjunto versionado | Não demonstrado |
| Parâmetros padrão da literatura | Bloco contínuo configura 30 lobos e 500 iterações; protocolo/origem dos parâmetros precisa ser explicitado | Parcial |
| Código modularizado e documentado | GWO está embutido no export Colab; motor PFS foi separado; solver DPFSP-DD é modular | Parcial |
| 30 execuções independentes | Código configura seeds 0–29 para três funções contínuas | Configurado no código; execução integral não comprovada por dados brutos versionados |
| Média e desvio padrão da convergência | Agregação e gráfico estão programados | Parcial; artefato final reproduzível não localizado |
| Reprodutibilidade | Seed explícita e testes de caracterização do legado | Parcial; falta empacotar o solver histórico e preservar os resultados por execução |

## 6. Recomendações corretivas

1. **Não reescrever o histórico.** Manter o GWO embutido no notebook e os resultados antigos identificados como legado.
2. **Não declarar a Semana 2 plenamente concluída.** O código de benchmark contínuo é evidência de teste auxiliar, não de validação Taillard/PFS.
3. **Manter DPFSP-DD como linha experimental própria.** O solver modular e o avaliador independente constituem uma implementação posterior para o problema efetivamente estudado, não substituem retroativamente a entrega Taillard da Semana 2.
4. **Se houver tempo e acesso às instâncias, completar uma validação PFS específica:** obter pelo menos duas instâncias Taillard, registrar fonte e hash, executar uma implementação PFS compatível com o benchmark e preservar os dados brutos das 30 seeds.
5. **Se a validação PFS não for viável antes da entrega, declarar a lacuna no artigo/apresentação.** Explicar a mudança de domínio para DPFSP-DD e apresentar separadamente a validação realizada nesse problema, sem alegar equivalência com Taillard.
6. **Para novas execuções, usar uma implementação versionada e importável.** Fixar a semântica de atualização (líderes congelados ou atualização sequencial), o schedule de `a`, o orçamento efetivo e os testes antes de gerar novos resultados.
7. **Não iniciar a bateria completa apenas para preencher o checklist.** Primeiro fechar a compatibilidade entre problema, parser, decoder e avaliador; depois executar um piloto limitado.

## 7. Conclusão

Há evidência de uma implementação própria do GWO contínuo e de código preparado para três funções de benchmark com 30 seeds. Entretanto, a implementação histórica possui atualização sequencial/in-place, o solver não está modularizado como módulo independente e não foi localizada a validação exigida em instâncias Taillard de PFS. A Semana 2 deve ser classificada como **parcialmente atendida**, com uma lacuna objetiva de benchmark e de rastreabilidade dos resultados.

O solver random-key para DPFSP-DD melhora a modularidade e a testabilidade do projeto atual, mas é uma implementação distinta e não elimina a lacuna histórica da Semana 2.
