# Plano de trabalho — GWO Environment

**Estado:** planejamento; nenhuma refatoração de código iniciada.  
**Protocolo associado:** [Protocolo experimental](../docs/experimental_protocol.md).

## Objetivo

Transformar o notebook/roteiro atual em um projeto Python reproduzível e modular, preservando o comportamento histórico identificável e executando uma comparação experimental confiável das versões Baseline, Tunado, Fuzzy e Surrogate nas 23 instâncias.

## Princípios e limites

- Preservar todos os arquivos e resultados originais.
- Não sobrescrever resultados históricos; novas execuções terão diretório/ID próprios.
- Não alterar silenciosamente o algoritmo GWO histórico. Distinguir variante sequencial existente de uma eventual implementação síncrona canônica.
- Corrigir bugs com testes e registrar alterações que afetem resultados.
- Falhar explicitamente quando uma instância estiver ausente ou inválida; nunca substituir por instância aleatória sem opção explícita.
- Toda execução registra parâmetros, seeds, ambiente, métricas e contadores reais.
- Nenhuma dependência nova, alteração de protocolo ou mudança de objetivo sem justificativa registrada.

## Arquitetura alvo (provisória)

```text
src/gwo_environment/
  algorithms/
    gwo.py
    gwo_fuzzy.py
  problems/
    flowshop.py
  surrogate/
    model.py
  optimization/
    optuna_tuning.py
  experiments/
    benchmark.py
    comparison.py
    statistics.py
  utils/
    instance_loader.py
    reproducibility.py
tests/
main.py
requirements.txt
docs/
  experimental_protocol.md
results/
  raw/
  processed/
  figures/
```

A arquitetura será ajustada à estrutura real do código durante a primeira etapa; não criar abstrações sem consumidor concreto.

## Fases

### Fase 1 — Congelar o protocolo e inventariar o comportamento

- [ ] Revisar o protocolo experimental e congelar as decisões do piloto.
- [ ] Inventariar as 23 instâncias e validar formato, dimensões e identificadores.
- [ ] Mapear funções/classes do script para módulos de destino.
- [ ] Registrar comportamento observável do GWO atual, incluindo atualização sequencial da população.
- [ ] Confirmar objetivo FlowShop e convenções de decodificação/empate.
- [ ] Definir esquema versionado dos resultados brutos.

**Checkpoint 1:** protocolo, dados e comportamento de referência documentados antes de mover/refatorar código.

### Fase 2 — Criar base executável e testes de caracterização

- [ ] Separar carregamento de instâncias e motor FlowShop.
- [ ] Criar testes para parser, decoder, cálculo do objetivo e casos inválidos.
- [ ] Criar testes de reprodutibilidade por seed e contagem de avaliações.
- [ ] Corrigir o bug de variável Fuzzy não definida.
- [ ] Corrigir métodos sem `self`/sem `@staticmethod`, se confirmado pelo uso.
- [ ] Remover dependências obrigatórias de `google.colab.files` da execução local, mantendo compatibilidade do notebook como interface opcional.
- [ ] Substituir instalação/upload/download interativos por configuração e caminhos explícitos.

**Checkpoint 2:** motor e algoritmo executam localmente em uma instância conhecida, com resultados de caracterização e testes.

### Fase 3 — Instrumentar e implementar o protocolo

- [ ] Implementar contadores reais e separados para objetivo, inferência, treino e validação.
- [ ] Implementar limites por orçamento de avaliações completas.
- [ ] Implementar execução em lote nas 23 instâncias e 30 seeds.
- [ ] Implementar ablação 2×2 (30/55 lobos × linear/quadrático).
- [ ] Integrar Fuzzy com comparação pareada contra GWO-55-Q.
- [ ] Reestruturar treino/teste do Surrogate por permutação decodificada.
- [ ] Reavaliar no FlowShop real a melhor solução do Surrogate.
- [ ] Implementar persistência incremental e retomada segura de execuções.

**Checkpoint 3:** piloto de três instâncias aprovado, contadores auditados e custos do Surrogate transparentes.

### Fase 4 — Bateria integral e análise

- [ ] Executar as seis configurações nas 23 instâncias com 30 seeds, registrando falhas.
- [ ] Validar completude, orçamento e integridade dos dados brutos.
- [ ] Gerar resumos por instância e porte.
- [ ] Gerar curvas de convergência por avaliações.
- [ ] Executar análise estatística pareada e corrigir comparações múltiplas.
- [ ] Gerar gráficos e tabelas reproduzíveis.
- [ ] Comparar novos resultados com os registros históricos sem fundi-los.

**Checkpoint 4:** conjunto bruto completo e análise reproduzível, com limitações explicitadas.

### Fase 5 — Entrega e documentação

- [ ] Criar `main.py` com comandos de execução documentados.
- [ ] Atualizar README com instalação, dados, execução e reprodução.
- [ ] Documentar arquitetura, parâmetros e protocolo final.
- [ ] Revisar código, testes, dados gerados e diferenças de comportamento.
- [ ] Fazer commit(s) pequenos e rastreáveis após validação.

## Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Instância ausente/parse inválido mascarado por fallback | Resultados inválidos | Erro explícito e validação prévia |
| Refatoração muda dinâmica do GWO | Não comparabilidade | Testes de caracterização e variantes identificadas |
| Contagem manual incorreta | Comparação injusta | Contadores na função real de avaliação |
| Surrogate memoriza permutações repetidas | Métricas de teste infladas | Split agrupado por permutação |
| Custo de treino omitido | Speedup enganoso | Tempo e avaliações separados e amortizados |
| Bateria extensa interrompida | Perda de trabalho | Persistência incremental, checkpoint e retomada |
| Poucas instâncias Large | Baixo poder estatístico | Análise descritiva e incerteza explícita |

## Critério de conclusão

Projeto executável localmente, com testes, protocolo congelado, resultados brutos reproduzíveis para as seis configurações e 23 instâncias, relatórios derivados e nenhuma perda dos artefatos históricos.
