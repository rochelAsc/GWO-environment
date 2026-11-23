# Proveniência dos datasets e escopo dos dados

- **Data:** 2026-11-22
- **Repositório auditado:** `rochelAsc/GWO-environment`, branch `main`
- **Confirmação do responsável pelo projeto:** os arquivos e conteúdos já mapeados são todo o material utilizado; não foi utilizado outro dataset ou conteúdo externo além desses. O responsável não recorda com precisão quais instâncias específicas alimentaram os experimentos PFS históricos.

## Inventário versionado

Em `data/` estão versionados:

- `data/instances/DPFSP_DD.zip`: conjunto DPFSP-DD auditado com 1.140 instâncias.
- `data/experimental/dados_brutos_4_versoes (1).csv`
- `data/experimental/historico_fuzzy (1).csv`
- `data/experimental/resultados_surrogate (1).csv`
- `data/experimental/resumo_small.csv`
- `data/experimental/tabela_4_versoes (1).csv`

Também existem relatórios, planilhas e o notebook histórico, mas não foi localizado um segundo arquivo independente de instâncias PFS em `data/instances/`.

## Interpretação permitida

O ZIP DPFSP-DD possui famílias Large identificadas por nomes `Ta...`; a auditoria estrutural registra que as matrizes de processamento das seis variantes de fábricas de cada família Large são compartilhadas, característica consistente com instâncias-base Taillard. O conjunto DPFSP-DD, contudo, acrescenta fábricas e due dates e não deve ser confundido com uma cópia bruta do benchmark PFS Taillard.

Os relatórios e resultados PFS antigos não identificam com evidência suficiente, no estado atual do repositório, o subconjunto exato de instâncias usado em cada execução. Portanto:

1. Não afirmar que as 23 instâncias do protocolo antigo são Taillard sem mapear nomes/arquivos e comprovar a correspondência.
2. Não fabricar ou baixar um dataset substituto para atribuí-lo retroativamente aos experimentos.
3. Preservar os resultados históricos, marcando a proveniência das instâncias PFS como não recuperada quando não houver evidência.
4. Se a execução PFS for necessária novamente, selecionar e documentar explicitamente um conjunto reproduzível, distinguindo-o do DPFSP-DD.

## Higiene do repositório

O inventário da árvore Git em 2026-11-22 encontrou cinco arquivos `.pyc` rastreados em `scripts/__pycache__/` e `tests/__pycache__/`. Os cinco foram removidos do repositório em commits separados. Nova leitura da árvore confirmou que não restam caminhos `__pycache__` nem arquivos `.pyc` rastreados. Os arquivos locais do usuário não foram tocados.
