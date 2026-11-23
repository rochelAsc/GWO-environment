# Caracterização do motor PFS legado

- **Data:** 2026-11-22
- **Status:** implementação estrita criada; execução da suíte local ainda pendente.
- **Escopo:** parser e avaliador PFS histórico embutidos no notebook Colab.

## Formato de arquivo caracterizado

O parser original fazia as seguintes suposições, agora explicitadas em `scripts/legacy_pfs.py`:

1. Primeira linha: `n_jobs n_machines`, ambos positivos.
2. Segunda linha não vazia: linha de metadados opaca, ignorada pelo código histórico.
3. Exatamente `n_jobs` linhas de processamento, cada uma com `n_machines` pares `machine_id processing_time`.
4. IDs de máquina zero-based, cada máquina exatamente uma vez por job.
5. Marcador único `Duedate`.
6. Exatamente uma due date não negativa por job.

A segunda linha foi mantida como metadado opaco porque o código anterior a ignorava sem interpretar seu conteúdo. **Não foi possível confirmar esse formato contra os arquivos PFS históricos originais**, pois eles não foram localizados no inventário do repositório. Os testes usam fixtures sintéticas construídas a partir das suposições do parser; não provam a identidade do benchmark nem que todos os arquivos antigos seguem esse formato.

## Implementação

Novo módulo `scripts/legacy_pfs.py`:

- `parse_legacy_pfs_text` e `load_legacy_pfs_instance`: parsing estrito.
- Arquivo inexistente gera `FileNotFoundError`; conteúdo inválido gera `ValueError` contextualizado.
- Não há fallback para dados aleatórios e não há alteração do estado global do NumPy.
- `carregar_instancia_txt` e `calcular_lower_bound_potts` são explicitamente `@staticmethod`.
- Construtor valida dimensões, valores inteiros, tempos positivos e due dates não negativas.
- Avaliador valida chaves/permutação e rejeita objetivos desconhecidos.
- A semântica PFS (uma sequência compartilhada por todas as máquinas) e o modo alternativo (uma sequência por máquina) foram preservados.

O notebook `notebooks/Sistemas_Inteligentes_Entregavel.ipynb` e o export `scripts/sistemas_inteligentes_entregavel.py` agora importam esse módulo em vez de manter uma cópia embutida do parser permissivo. A execução exige que o repositório esteja disponível a partir do diretório de trabalho; se o módulo não estiver presente, a execução falha explicitamente.

## Testes adicionados

`tests/test_legacy_pfs.py` cobre:

- parsing válido e reordenação dos pares de máquina;
- arquivo ausente e entradas malformadas;
- acesso dos métodos estáticos pela classe e pela instância;
- tardiness e makespan em schedules conhecidos;
- comparação com recorrência independente de tempos de conclusão;
- modo com sequências por máquina;
- validação de permutações e arrays;
- lower bound em um caso manual;
- rejeição de objetivo inválido.

A suíte contém 20 casos após expansão dos testes parametrizados. Ela ainda precisa ser executada no ambiente local do projeto; nenhum resultado de teste é declarado neste documento.

## Limitações preservadas

- O GWO legado sequencial/in-place não foi alterado.
- A formulação e validade matemática do lower bound de Potts não foram reavaliadas nesta etapa; apenas seu contrato de método e validação de entradas foram tratados.
- Não foi feita equivalência de resultados com instâncias históricas, pois o subconjunto original de arquivos PFS não foi recuperado.
- O motor permanece específico do PFS legado e não substitui o avaliador DPFSP-DD.
