# Semana 2 — Reconstrução experimental do GWO baseline

## Objetivo

Reconstruir a etapa de implementação e validação do solver usando o problema originalmente especificado no roteiro: Permutation Flow Shop Problem (PFSP), com instâncias Taillard e minimização de makespan. Esta reconstrução é uma nova execução versionada; não substitui nem reescreve resultados históricos de PFS com datas de entrega ou de DPFSP-DD.

## Instâncias

| Instância | Jobs | Máquinas | Seed de geração | UB publicado | LB publicado |
|---|---:|---:|---:|---:|---:|
| ta001 | 20 | 5 | 873654221 | 1278 | 1232 |
| ta011 | 20 | 10 | 587595453 | 1582 | 1448 |

Os arquivos foram obtidos do espelho PISCO do conjunto Taillard e serão versionados no repositório com SHA-256 no arquivo de metadados de cada execução. A referência primária é Taillard (1993), *Benchmarks for basic scheduling problems*, European Journal of Operational Research, 64(2), 278–285, DOI 10.1016/0377-2217(93)90182-M. O objetivo original do conjunto é minimizar makespan em problemas de flow shop sem datas de entrega.

Espelho dos arquivos:
- https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard

## Formulação

Cada job (j) deve ser processado, na mesma ordem de jobs, nas (m) máquinas. Para uma permutação (pi), os tempos de conclusão são:

[
C_{pi_k,1}=C_{pi_{k-1},1}+p_{pi_k,1}
]

[
C_{pi_k,i}=max(C_{pi_{k-1},i},C_{pi_k,i-1})+p_{pi_k,i}
]

com (C_{pi_0,i}=C_{pi_k,0}=0). A função objetivo é minimizar:

[
C_{max}(pi)=C_{pi_n,m}.
]

## Representação e algoritmo

O indivíduo é um vetor contínuo de (n) random keys em ([0,1]). A permutação é obtida por ordenação estável crescente das chaves. O solver aplica as equações GWO de alpha, beta e delta, com:
- 30 lobos;
- 500 iterações;
- parâmetro (a(t)=2-2t/T);
- atualização síncrona: todos os lobos usam os mesmos líderes congelados no início da geração;
- clipping das posições para ([0,1]);
- 30 seeds independentes (0 a 29).

A implementação do solver é própria e usa NumPy apenas para operações numéricas; não usa framework de otimização.

## Orçamento

A população inicial é avaliada uma vez e cada geração avalia todos os lobos. Logo:

[
N_{mathrm{eval}}=N_{mathrm{wolves}}(T+1)=30(500+1)=15030
]

por execução e instância. Para duas instâncias e 30 seeds: 60 execuções e 901.800 avaliações de makespan.

## Artefatos gerados

O script `scripts/run_week2_benchmark.py` produz:
- `runs.csv`: uma linha por instância/seed, com fitness, tempo, avaliações e permutação;
- `convergence.csv`: média e desvio padrão amostral do melhor makespan por geração;
- `metadata.json`: protocolo, ambiente, seeds, hashes dos arquivos, limites publicados e estatísticas agregadas.

## Critérios de validação

- parser confere dimensões e número de tempos;
- avaliador é testado contra casos calculados manualmente e enumeração exaustiva de instância pequena;
- decoder sempre retorna uma permutação, com desempate estável;
- execução com mesma seed deve produzir exatamente o mesmo resultado;
- contador de avaliações deve ser (N(T+1));
- melhor histórico é monotônico por construção do arquivo de líderes.

Os valores UB/LB publicados são referências de qualidade. O UB é um limite superior conhecido, não necessariamente o ótimo provado; o gap calculado em relação a ele será identificado como distância ao UB publicado, não como optimality gap.

## Referência

Taillard, E. (1993). Benchmarks for basic scheduling problems. *European Journal of Operational Research*, 64(2), 278–285. https://doi.org/10.1016/0377-2217(93)90182-M
