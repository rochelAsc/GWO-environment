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

### DEC-DPFSP-008 — separar erros de dados de erros de programação no validador
O script de validação registra apenas erros esperados de entrada: texto que não seja UTF-8 válido e `ValueError` emitido pelo parser para dados malformados. Exceções inesperadas, como `TypeError` causado por defeito interno ou erros de leitura do ZIP, propagam-se e interrompem a execução. Essa escolha evita que bugs sejam apresentados como simples instâncias inválidas. O script também falha explicitamente se não encontrar nenhum arquivo candidato.

## Evidências de validação

### Testes automatizados
Execução reportada pelo usuário em Windows, com Python 3.14 e pytest 9.2.0:

```text
.................... [100%]
20 passed, 1 warning in 0.04s
```

Os 20 testes passaram, incluindo os quatro casos manuais, entradas inválidas, parser sintético e enumeração exaustiva dos 120 cronogramas da instância pequena. O único aviso vem do plugin `anyio`, que importa o alias `CallSpec2` do pytest; é um aviso de compatibilidade/depreciação do plugin, não uma falha dos testes do projeto.

### Dataset real
O parser foi executado em todas as entradas candidatas do ZIP real. O relatório versionado em `results/parser_validation/summary.json` registra **1.140 arquivos candidatos, 1.140 interpretações bem-sucedidas e zero falhas**. As distribuições de jobs, máquinas e fábricas coincidem com a auditoria estrutural anterior.

### Interpretação e limites
As evidências atuais sustentam que os testes implementados passam no ambiente reportado e que o parser interpreta estruturalmente todas as instâncias candidatas do ZIP. Isso não substitui uma revisão da formulação matemática contra a literatura, nem constitui validação de qualquer algoritmo GWO. A especificação DPFSP-DD continua em rascunho para revisão.

Nenhum resultado experimental de otimização foi produzido por esta etapa.

## Próxima etapa metodológica

Antes de implementar GWO, consultar o artigo original de Mirjalili et al. sobre Grey Wolf Optimizer em fonte web primária/fiável. Mapear cada equação e operador do artigo para o código. Qualquer adaptação para permutações/DPFSP-DD será registrada como decisão separada, com justificativa, consequência e teste correspondente. Não assumir aplicação direta do GWO contínuo a sequências discretas sem representação/decodificação explícita.
