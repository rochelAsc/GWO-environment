# Lista de tarefas — GWO Environment

## Fase 1 — Protocolo e inventário
- [ ] Revisar e congelar o protocolo após o piloto.
- [ ] Inventariar e validar as 23 instâncias do arquivo compactado.
- [ ] Mapear funções/classes do script atual e dependências.
- [ ] Registrar a dinâmica histórica do GWO e as regras de decodificação.
- [ ] Definir schema versionado para os resultados.

## Fase 2 — Base executável e testes
- [ ] Separar parser e motor FlowShop com testes.
- [ ] Criar testes de decoder e função objetivo.
- [ ] Criar testes de seed, determinismo e contagem de avaliações.
- [ ] Corrigir o erro de nome em execução Fuzzy.
- [ ] Corrigir contratos de métodos estáticos, após confirmar chamadas.
- [ ] Desacoplar execução local das APIs interativas do Colab.

## Fase 3 — Experimentos
- [ ] Implementar contadores e orçamento efetivo.
- [ ] Implementar runner para instâncias/seeds e persistência incremental.
- [ ] Implementar ablação fatorial 2×2.
- [ ] Integrar e instrumentar Fuzzy.
- [ ] Implementar split de Surrogate agrupado por permutação.
- [ ] Validar a solução Surrogate com o FlowShop real.
- [ ] Executar e aprovar piloto em três instâncias.

## Fase 4 — Bateria e análise
- [ ] Executar as seis configurações nas 23 instâncias e 30 seeds.
- [ ] Auditar completude, contadores e falhas.
- [ ] Gerar métricas e curvas de convergência.
- [ ] Executar estatística pareada por instância e porte.
- [ ] Gerar tabelas e figuras a partir dos dados brutos.

## Fase 5 — Entrega
- [ ] Criar interface de execução em main.py.
- [ ] Atualizar README e documentação de reprodução.
- [ ] Revisar testes e diferenças de comportamento.
- [ ] Preparar commits rastreáveis.
