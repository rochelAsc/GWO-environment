> **REVISÃO CRÍTICA — piloto Fuzzy v1 inválido para avaliar adaptação por diversidade.** O solver Fuzzy também não substituía `positions` por `new_positions`. A diversidade registrada ficou constante dentro de cada execução, então o controlador não observou a evolução da população. O piloto e os CSVs v1 são preservados como evidência do defeito, não como resultado válido do controlador adaptativo. A versão v2 corrige a dinâmica; um novo piloto curto deve ser executado contra a baseline e o tuning v2. Nenhuma bateria de 30 seeds deve ser executada antes de inspecionar esse piloto.

# Semana 5 — Auditoria da reconstrução Fuzzy

**Status atual:** solver v2 e teste de regressão publicados; CI e piloto v2 pendentes. As informações de execução abaixo descrevem o histórico v1 e não validam adaptação Fuzzy.

## Evidência histórica

O arquivo `data/experimental/historico_fuzzy (1).csv` contém 100 registros de iteração, fator de ajuste e valor de `a`. Não contém as variáveis de entrada do controlador, funções de pertinência, regras, método de inferência, defuzzificação, instância ou seed. Logo, não há informação suficiente para reproduzir fielmente o controlador histórico. O CSV permanece imutável e não é usado como resultado da reconstrução.

## Implementação nova

Foram adicionados:
- `scripts/fuzzy_controller.py`: pertinências, regras Mamdani, agregação min-max, centroide e métrica de diversidade;
- `scripts/gwo_pfs_fuzzy.py`: GWO síncrono com controle Fuzzy de `a`;
- `scripts/run_week5_fuzzy.py`: avaliação pareada contra baseline Semana 2 e tunado Semana 3;
- `tests/test_week5_fuzzy.py`: testes de limites, validação, reprodutibilidade e orçamento;
- `docs/reports/week5_fuzzy_protocol.md`: especificação completa.

O protocolo usa PFSP/Taillard, makespan, 30 lobos, 500 iterações, 15.030 avaliações por execução e seeds 0–29. O piloto recomendado usa seeds 0, 1 e 2. A comparação v2 usa os resultados corrigidos das Semanas 2 e 3, sem sobrescrever os diretórios v1.

## Controlador

Entradas: diversidade média par-a-par no espaço de random keys e estagnação medida por gerações consecutivas sem melhoria, normalizada por janela 20. Saída: multiplicador de exploração [0,5; 1,5], aplicado à agenda linear de referência. O controlador usa três conjuntos linguísticos por entrada e saída, nove regras, inferência Mamdani min-max e centroide numérico.

Essas escolhas constituem uma reconstrução nova e transparente. Não devem ser atribuídas retroativamente ao experimento original.

## Próximas verificações

1. Confirmar CI para os novos módulos e testes.
2. Executar o piloto de três seeds nas duas instâncias.
3. Inspecionar contadores, convergência, estabilidade, traço Fuzzy e comparações pareadas.
4. Somente então autorizar a bateria de 30 seeds.

Nenhuma conclusão de desempenho ou superioridade é possível antes da execução experimental.
