# Decisões de escopo — atualização de 22/11/2026

**Origem:** respostas do autor após a auditoria inicial e orientação verbal do professor.  
**Natureza:** adendo de planejamento; não altera nem substitui os documentos, dados ou resultados históricos.

## 1. Roteiro e Meta-Learning

O roteiro publicado continua sendo a referência do trabalho, com uma alteração explícita determinada pelo professor: **a etapa de Meta-Learning foi retirada**. Como não foi indicado um conteúdo substituto, não será criada uma etapa artificial para ocupar esse espaço.

Consequências:
- Não implementar classificador/recomendador de solver como requisito do projeto.
- Não construir meta-dataset nem reivindicar resultados de Meta-Learning.
- Manter a comparação experimental dos algoritmos como foco do trabalho e do artigo.
- Preservar o roteiro original como registro histórico; esta decisão documenta a orientação posterior.

## 2. Duas famílias de problemas

O estudo contemplará duas famílias, tratadas como experimentos separados:

1. **Permutation Flow Shop (PFS) clássico**, incluindo validação com instâncias Taillard, conforme a etapa de baseline do roteiro.
2. **Distributed Permutation Flow Shop com due dates (DPFSP-DD)**, usando o conjunto de instâncias existente no repositório, após inspeção do ZIP e confirmação da formulação.

Não assumir equivalência entre PFS e DPFSP-DD. Cada família exige representação, parser, decoder, função objetivo e protocolo compatíveis com sua formulação. Resultados de famílias diferentes não serão agregados como se viessem do mesmo problema.

A aplicabilidade de cada uma das quatro versões (Baseline, Tunado, Fuzzy e Surrogate) e das ablações será verificada por família. Se uma implementação não for válida para determinada formulação, isso será registrado; não se forçará uma comparação incompatível.

## 3. Algoritmos e ablações

Permanecem como eixo principal as quatro versões solicitadas pelo professor:
- Baseline;
- Tunado;
- Fuzzy;
- Surrogate.

Também serão mantidas as duas configurações de ablação já propostas:
- 30 lobos com decaimento quadrático;
- 55 lobos com decaimento linear.

A comparação deve controlar o orçamento de avaliações e explicitar quais variantes são comparáveis em cada família de problemas. A matriz final de experimentos e o número total de execuções só serão congelados depois de confirmar instâncias, implementações e piloto.

## 4. Validação cruzada do Surrogate

A validação cruzada será incorporada ao estudo do modelo substituto, mas seus detalhes ainda não estão congelados.

Requisitos já estabelecidos:
- Agrupar amostras pela **permutação efetivamente decodificada**. Representações contínuas diferentes que gerem a mesma permutação não podem cair em folds distintos.
- Separar validação do modelo da avaliação do otimizador.
- Não usar o fold de teste para seleção de hiperparâmetros ou decisões que depois sejam reportadas como avaliação independente.
- Avaliar também a melhor solução encontrada pelo Surrogate na função objetivo real.
- Registrar a variabilidade entre folds e o número de permutações únicas por fold.

Ainda precisam de decisão fundamentada em literatura e discussão com o autor: estratégia e número de folds, repetição das partições, necessidade de validação aninhada para sintonia e tratamento de instâncias com poucas permutações únicas. Nenhuma dessas escolhas deve ser definida apenas por conveniência.

## 5. Sintonia e fundamentação científica

Uma nova sintonia com Optuna é permitida. Espaço de busca, limites, distribuições, orçamento, métrica-alvo e critérios de seleção devem ser justificados por literatura pertinente e registrados.

Toda decisão metodológica relevante deve:
1. apresentar a alternativa e sua justificativa;
2. identificar a evidência bibliográfica ou matemática;
3. explicitar vantagens, limitações e possíveis vieses;
4. ser discutida com o autor antes de ser congelada no protocolo.

Resultados exploratórios antigos serão preservados. Se uma auditoria identificar erro que invalide uma métrica ou execução, os experimentos afetados serão refeitos em novos arquivos/IDs, sem sobrescrever os originais.

## 6. Ambiente computacional

O desenvolvimento deve buscar compatibilidade com execução local e Kaggle. A escolha do ambiente de produção será baseada em medições do piloto, não na suposição de que GPU sempre acelera o código.

Registrar:
- CPU, GPU, RAM e sistema operacional;
- versões de Python e bibliotecas;
- tempo de instalação, preparação dos dados, treino e execução;
- uso efetivo de GPU, quando aplicável;
- limites de sessão, memória e armazenamento da plataforma.

Bibliotecas como scikit-learn podem executar modelos MLP em CPU mesmo quando há GPU disponível; portanto, a disponibilidade de GPU no Kaggle não implica aceleração automática. A implementação e as dependências serão verificadas antes de decidir onde rodar a bateria integral.

## 7. Próxima sequência de trabalho

1. Inspecionar o conteúdo e a estrutura do ZIP DPFSP-DD.
2. Confirmar formalmente a formulação e a compatibilidade do motor legado.
3. Obter e validar instâncias Taillard para o experimento PFS clássico, registrando origem, licença e hashes.
4. Definir a matriz de aplicabilidade dos algoritmos por família.
5. Auditar e corrigir os motores em implementação nova, com testes.
6. Fundamentar e discutir as escolhas de validação cruzada e sintonia.
7. Executar pilotos por família e ambiente computacional.
8. Congelar protocolos separados antes das baterias completas.

**Nenhum resultado novo de benchmark é declarado neste adendo.**