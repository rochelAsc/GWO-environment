# Registro de implementação — avaliador DPFSP-DD

- **Data:** 2026-11-22
- **Escopo:** modelo de dados, parser de instâncias em texto, avaliador determinístico e testes unitários.
- **Fora do escopo:** GWO, Fuzzy, Surrogate, PFS clássico e benchmarks.
- **Especificação:** [DPFSP-DD com Total Tardiness](../specifications/dpfsp_dd_spec.md), ainda em rascunho para revisão.

## Decisões registradas

### DEC-DPFSP-001 — avaliador independente da representação do algoritmo
O avaliador recebe exatamente F sequências já decodificadas. Não conhece vetores contínuos, random keys, operadores ou regras de reparo. Isso reduz acoplamento e permite testar o objetivo sem envolver o otimizador.

### DEC-DPFSP-002 — modelo imutável e sem dependência numérica
DPFSPInstance armazena matriz de processamento, due dates e número de fábricas em tuplas imutáveis. A implementação usa inteiros Python e não depende de NumPy. A escolha evita coerção silenciosa de tipos e torna a avaliação reproduzível.

### DEC-DPFSP-003 — parser estrito
O parser interpreta a primeira linha como n,m, a segunda como F, depois n linhas de pares (machine_id, processing_time), o marcador Duedate e n due dates. Os pares são colocados por identificador de máquina, não pela posição em que aparecem na linha. Índices internos são zero-based.

O parser rejeita cabeçalhos malformados, linhas faltantes/extras, identificadores de máquina repetidos/fora do intervalo, tempos não positivos, due dates negativas e marcadores ausentes ou duplicados. Não há fallback aleatório.

### DEC-DPFSP-004 — recorrência por fábrica
Para cada job na sequência de uma fábrica, a conclusão na máquina k é p[j,k] + max(conclusão do job anterior na mesma máquina, conclusão do mesmo job na máquina anterior). A disponibilidade das máquinas é reiniciada em cada fábrica, pois fábricas idênticas operam independentemente.

### DEC-DPFSP-005 — fábricas vazias válidas
A validação exige exatamente F sequências, mas permite sequências vazias. Cada job precisa aparecer uma única vez no conjunto das sequências.

### DEC-DPFSP-006 — falha explícita para soluções inválidas
Jobs ausentes, duplicados, fora do intervalo, índices negativos e quantidade incorreta de sequências geram exceções. O avaliador não repara nem descarta silenciosamente elementos.

### DEC-DPFSP-007 — saída auditável
Além de Total Tardiness, o resultado inclui conclusão e tardiness por job, fábrica/posição de cada job e tempos de conclusão de todas as operações por fábrica, posição e máquina.

## Validação e pendências

- Os testes cobrem os quatro casos manuais da especificação, entradas inválidas e parser sintético com pares de máquinas fora de ordem.
- **Pendente:** executar os testes com exemplos reais extraídos de DPFSP_DD.zip e conferir manualmente um Small e um Large, incluindo F, matriz P e vetor d.
- **Pendente:** comparar o avaliador com implementação independente ou enumeração exaustiva em instâncias minúsculas antes de liberar experimentos.
- Nenhum resultado experimental foi produzido por esta alteração.

## Próxima etapa metodológica

Antes de implementar GWO, consultar o artigo original de Mirjalili et al. sobre Grey Wolf Optimizer em fonte web primária/fiável. Mapear cada equação e operador do artigo para o código. Qualquer adaptação para permutações/DPFSP-DD será registrada como decisão separada, com justificativa, consequência e teste correspondente. Não assumir aplicação direta do GWO contínuo a sequências discretas sem representação/decodificação explícita.
