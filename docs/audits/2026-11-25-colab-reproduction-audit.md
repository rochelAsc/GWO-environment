# Auditoria da reprodução no Google Colab

**Data da auditoria:** 25/11/2026 (horário local; manifesto gerado em 26/11/2026 UTC)  
**Execução:** `colab_20261125_01`  
**Commit do código executado:** `8c09b360c01227e215e1e037441eb662c19502ba`  
**Commit de publicação dos artefatos:** `d6da04ffd20c4b0d0908f97c60d300dc088bb13d`  
**Diretório auditado:** `results/notebook_runs/colab_20261125_01/`  
**Notebook:** `notebooks/Sistemas_Inteligentes_Entregavel.ipynb`

## 1. Escopo e veredito

Esta auditoria verifica os artefatos produzidos pela execução do notebook no Google Colab e publicados no repositório. O objetivo é avaliar completude estrutural, rastreabilidade, coerência dos contadores e consistência dos resultados com as baterias locais previamente auditadas.

**Veredito:** os artefatos das Semanas 2 a 6 estão presentes e estruturalmente completos. Os resultados por instância e seed das variantes Baseline, Optuna e Fuzzy coincidem com os respectivos resultados incorporados à bateria da Semana 6. Os contadores da estratégia Surrogate também conferem com o protocolo. Não foi identificada divergência de makespan nas 180 correspondências verificadas.

A auditoria não equivale a uma reprodução bit a bit de todo o ambiente nem comprova que cada célula do notebook terminou sem erro: o ZIP publicado não contém um log integral da execução das células nem uma saída persistida que comprove o resultado do comando de testes.

## 2. Identificação e ambiente

O manifesto `execution_manifest.json` registra:

- RUN_ID: `colab_20261125_01`;
- branch: `main`;
- commit do código executado: `8c09b360c01227e215e1e037441eb662c19502ba`;
- Python 3.13.18;
- Linux x86_64, kernel 6.6.159+;
- NumPy 2.4.6, SciPy 1.16.3, scikit-learn 1.6.1, pandas 2.2.3, Optuna 4.9.0, Matplotlib 3.10.0, joblib 1.6.0 e pytest 8.4.2.

Os hashes SHA-256 das instâncias Taillard registrados no manifesto coincidem com os hashes usados nos metadados locais:

| Instância | SHA-256 |
|---|---|
| ta001 | `2b0277746a8bdf0da424f4cde45779432ca75ce7c5fafddedc914c82d6483432` |
| ta011 | `dadcba033e965f2cbf99ef5d1220553e2e974a15250add72bceea415f813c628` |

O manifesto identifica o commit do código utilizado, enquanto o commit de publicação identifica a inclusão dos resultados na branch. São referências distintas e não devem ser confundidas.

## 3. Completude dos artefatos

| Etapa | Evidência publicada | Verificação |
|---|---|---|
| Semana 1 | Registro documental no notebook | Não há pipeline dengue/LSTM executável a reproduzir no estado atual do projeto |
| Semana 2 | 60 execuções, convergência e metadados | 30 seeds por instância; 15.030 avaliações por execução |
| Semana 3 | 30 trials Optuna, banco SQLite, parâmetros, gráficos e 60 avaliações finais | 30 trials concluídos; avaliação final em 2 instâncias × 30 seeds |
| Semana 4 | 2 datasets, 2 modelos, métricas e gráficos | 2.000 permutações únicas por instância; divisão 1.600/400 |
| Semana 5 | 60 execuções, convergência, resumo e rastreamento fuzzy | 30 seeds por instância |
| Semana 6 | 240 execuções, convergência, resumo, estatísticas e rastreamentos | 4 variantes × 2 instâncias × 30 seeds |

A Semana 1 é documental: o notebook registra a mudança de escopo do tema inicial dengue/LSTM para PFSP/Taillard. Não se deve descrever essa etapa como experimento executado no Colab.

## 4. Consistência dos resultados

### 4.1 Correspondência entre as semanas

Foram comparados os makespans por instância e seed entre os resultados independentes das Semanas 2, 3 e 5 e as respectivas variantes da Semana 6:

| Comparação | Pares verificados | Correspondências |
|---|---:|---:|
| Semana 2 Baseline × Semana 6 Baseline | 60 | 60 |
| Semana 3 Optuna × Semana 6 Optuna | 60 | 60 |
| Semana 5 Fuzzy × Semana 6 Fuzzy | 60 | 60 |
| **Total** | **180** | **180** |

Não foram encontradas divergências nos makespans dessas 180 correspondências. Essa verificação confirma consistência dos resultados registrados; não prova igualdade de todos os estados internos ou trajetórias aleatórias.

### 4.2 Contadores da Semana 6

A bateria contém 240 registros, distribuídos igualmente:

| Variante | Execuções | Avaliações exatas por execução | Predições por execução |
|---|---:|---:|---:|
| Baseline | 60 | 15.030 | 0 |
| Optuna | 60 | 15.030 | 0 |
| Surrogate | 60 | 1.530 | 15.000 |
| Fuzzy | 60 | 15.030 | 0 |

Os contadores observados nos arquivos por execução conferem com o protocolo. O total da busca é de 2.797.200 avaliações exatas e 900.000 predições surrogate. A preparação dos dois modelos da Semana 4 gerou 4.000 rótulos exatos adicionais, contabilizados separadamente da busca.

### 4.3 Resultados agregados da Semana 6

Os resumos publicados no Colab reproduzem os resultados da bateria local:

| Instância | Baseline | Optuna | Surrogate | Fuzzy |
|---|---:|---:|---:|---:|
| ta001 — média | 1272,73 | 1268,40 | 1275,13 | 1269,10 |
| ta011 — média | 1640,23 | 1638,77 | 1660,20 | 1633,83 |

As estatísticas de Friedman e as comparações pareadas com correção de Holm também são consistentes com a bateria local: em `ta001`, nenhuma comparação par a par permanece significativa após Holm; em `ta011`, as três comparações envolvendo Surrogate apontam desempenho inferior dessa variante.

A interpretação estatística e as limitações permanecem as mesmas da [auditoria da Semana 6](2026-11-25-week6-benchmark-audit.md).

## 5. Integridade e limitações da verificação

Verificações realizadas:

- presença dos arquivos esperados nas pastas das Semanas 2 a 6;
- presença dos modelos `.joblib`, datasets, gráficos, bancos e rastreamentos;
- hashes das instâncias registrados no manifesto;
- quantidade de linhas de dados nos CSVs principais;
- 30 trials Optuna e 60 avaliações finais;
- 240 execuções na Semana 6, sem chaves duplicadas de variante/instância/seed;
- contadores de avaliações exatas e predições;
- correspondência dos makespans nas 180 comparações entre semanas.

Limitações:

1. **Log de execução:** o pacote não preserva um log integral com saída de todas as células. Em particular, não há evidência persistida suficiente para atestar pelo pacote que o `pytest` executado nessa sessão terminou com sucesso.
2. **Reprodução bit a bit:** não foi exigido que CSVs tivessem os mesmos bytes, pois diferenças de finais de linha CRLF/LF podem ocorrer entre Windows e Linux. A comparação realizada foi lógica, por registros, chaves, contadores e makespans.
3. **Ambiente:** o Colab usou Python 3.13.18/Linux; a bateria local foi registrada em Windows 11/Python 3.14.6. Portanto, tempos e bytes de artefatos não são critérios de igualdade.
4. **Semana 1:** não houve execução de pipeline dengue/LSTM; a célula é registro de escopo e histórico.
5. **Generalização:** a reprodução confirma consistência nas duas instâncias Taillard avaliadas, não generalização para outras instâncias.

## 6. Conclusão

A reprodução do notebook no Colab produziu os artefatos experimentais esperados para as Semanas 2 a 6. As 180 correspondências de makespan entre as baterias independentes e a Semana 6, além dos contadores completos da Semana 6, sustentam a consistência dos resultados publicados.

**Status:** reprodução experimental das Semanas 2–6 auditada quanto à completude dos artefatos e consistência dos resultados. A execução integral das células e a aprovação do `pytest` nessa sessão permanecem não comprovadas pelo pacote publicado.
