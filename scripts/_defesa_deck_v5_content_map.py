"""Content map for defesa deck v5: takeaways + 4-beat speaker notes.

Numbers must match the audited v3/v4 deck. Do not invent metrics here.
"""
from __future__ import annotations

# Each entry: notes (required), takeaway (optional on-slide callout), lead (optional).
# takeaway=None means leave existing callouts as-is unless replace_callout=True.
# replace_callout=True replaces the first .callout (non-warn) or inserts before footer.

SLIDES: dict[int, dict[str, str | bool | None]] = {
    1: {
        "lead": (
            "Defender a cadeia de evidências do GWO no PFSP: o que foi executado, "
            "o que os dados sustentam — inclusive nulos e negativos — e o que ainda é extensão aberta."
        ),
        "notes": (
            "Gancho: delimite o núcleo — GWO no PFSP clássico com makespan, semanas 1–6. "
            "Olhar: três pontos Problema/Objetivo/Método; a tese está no lead. "
            "Não concluir: extensões surrogate/meta não são a entrega central nem estão fechadas. "
            "Ponte: as RQs organizam o que cada bloco precisa provar."
        ),
    },
    2: {
        "notes": (
            "Gancho: quatro perguntas, quatro tipos de evidência. "
            "Olhar: RQ1→auditoria/código; RQ2–RQ3→Week 6; Extensões→curva/modelos/meta. "
            "Não concluir: curva de aprendizagem não mede qualidade do GWO; meta-learning não é surrogate. "
            "Ponte: hipóteses e critérios vêm antes dos números."
        ),
    },
    3: {
        "takeaway": "Hipóteses pré-registradas guiam a leitura; nenhuma foi presumida confirmada.",
        "replace_callout": True,
        "notes": (
            "Gancho: mostre o contrato antes dos resultados. "
            "Olhar: coluna Critério — Optuna com orçamento igual; Surrogate no compromisso qualidade-custo; meta por instância. "
            "Não concluir: critério ≠ vitória; resultados nulos também contam. "
            "Ponte: formular o PFSP e a representação random keys."
        ),
    },
    4: {
        "notes": (
            "Gancho: o objeto é uma permutação, não um contínuo abstrato. "
            "Olhar: Cmax = C_πn,m e a recorrência; UBs 1278/1582 são referência publicada. "
            "Não concluir: diferença para UB não é optimality gap de ótimo conhecido. "
            "Ponte: como o GWO contínuo gera essa permutação."
        ),
    },
    5: {
        "takeaway": "Fitness usa makespan exato da permutação decodificada — nunca aproximação silenciosa.",
        "notes": (
            "Gancho: ponte contínuo → discreto. "
            "Olhar: fluxo x → argsort → Cmax; líderes αβδ e substituição síncrona da população. "
            "Não concluir: calcular new_positions sem atribuir não é GWO iterativo — isso volta na auditoria. "
            "Ponte: a matemática da atualização usada no código."
        ),
    },
    6: {
        "notes": (
            "Gancho: esta é a dinâmica implementada, não um catálogo de variantes teóricas. "
            "Olhar: média de X1–X3, clipping [0,1], a(t) baseline vs Optuna vs Fuzzy. "
            "Não concluir: arquivo elite e líderes congelados são adaptação concreta do projeto. "
            "Ponte: linha do tempo das semanas e onde a falha v1 aparece."
        ),
    },
    7: {
        "takeaway": "A sequência não é linear: a auditoria forçou reconstruir Baseline, Optuna e Fuzzy.",
        "notes": (
            "Gancho: mapa cronológico com o ponto de ruptura. "
            "Olhar: bloco AUD entre S5 e S6; Semana 4 fora do defeito populacional. "
            "Não concluir: resultados v1 como desempenho. "
            "Ponte: Semana 1 — por que o escopo é PFSP."
        ),
    },
    8: {
        "notes": (
            "Gancho: transparência de escopo, se perguntarem. "
            "Olhar: escopo consolidado = PFSP/Taillard; o que conta = código, seeds, logs. "
            "Não concluir: materiais iniciais de dengue/LSTM como experimento executado. "
            "Ponte: protocolo experimental comum."
        ),
    },
    9: {
        "notes": (
            "Gancho: ficha que vale para o estudo principal. "
            "Olhar: unidade = instância×seed; ta001/ta011; Friedman/Wilcoxon/Holm por instância. "
            "Não concluir: seeds iguais = RNG idêntico entre implementações. "
            "Ponte: Baseline v2 como referência."
        ),
    },
    10: {
        "takeaway": "Baseline fixa o comparador simples sob 15.030 avaliações exatas por run.",
        "notes": (
            "Gancho: sem baseline não há Δ defensável. "
            "Olhar: 30×501=15.030; médias 1272,73 e 1640,23 — só referência, não ranking final. "
            "Não concluir: usar qualquer resultado v1. "
            "Ponte: Optuna sob o mesmo orçamento exato."
        ),
    },
    11: {
        "takeaway": "Melhoria média pequena (−4,33 / −1,47) não prova superioridade estatística.",
        "notes": (
            "Gancho: tuning separado da avaliação. "
            "Olhar: seeds 100–102 vs 0–29; 45×334=15.030; Δ na última coluna. "
            "Não concluir: Optuna “venceu” só pela média. "
            "Ponte: surrogate — outro contrato de custo."
        ),
    },
    12: {
        "takeaway": "RMSE/Spearman medem ajuste global; não garantem recuperar os melhores schedules.",
        "notes": (
            "Gancho: aprender Cmax de permutações aleatórias. "
            "Olhar: ta001 R² 0,573 / ρ 0,758 vs ta011 0,252 / 0,539 — qualidade cai com a instância. "
            "Não concluir: bom ranking global = bom top-k operacional. "
            "Ponte: custo de inferência e break-even."
        ),
    },
    13: {
        "takeaway": "Microbenchmark de lote ≠ speedup do GWO completo.",
        "notes": (
            "Gancho: onde a vantagem de tempo aparece. "
            "Olhar: speedup em lote 3,31×/5,45×; break-even milhares de consultas. "
            "Não concluir: aceleração automática do algoritmo completo. "
            "Ponte: Fuzzy modula exploração, não a função objetivo."
        ),
    },
    14: {
        "takeaway": "Fuzzy multiplica a(t); não troca o makespan exato como critério.",
        "notes": (
            "Gancho: controle adaptativo de exploração. "
            "Olhar: entradas D e S; saída [0,5; 1,5] no acoplamento a(t). "
            "Não concluir: retunar regras depois de ver Week 6. "
            "Ponte: a falha que invalidou a v1."
        ),
    },
    15: {
        "notes": (
            "PAUSA. Gancho: este é o ponto retórico central da validade (RQ1). "
            "Olhar: fluxo vermelho — new_positions avaliadas sem positions = new_positions. "
            "Não concluir: elite atualizado = população avançando; v1 não é GWO iterativo. "
            "Ponte: correção v2 e o que a CI realmente prova."
        ),
    },
    16: {
        "takeaway": "CI com 100 testes valida regressão de software — não substitui o benchmark de 30 seeds.",
        "notes": (
            "Gancho: separar teste de software de evidência experimental. "
            "Olhar: atribuição síncrona; diversidade Fuzzy atualizada; métrica CI datada 23/11. "
            "Não concluir: suíte atual tem o mesmo tamanho; CI ≠ generalização. "
            "Ponte: Fuzzy v2 descritivo, depois o desenho Week 6."
        ),
    },
    17: {
        "takeaway": "Diferenças descritivas Fuzzy vs Baseline/Optuna não foram estatisticamente significativas.",
        "replace_callout": True,
        "notes": (
            "Gancho: números Fuzzy antes do benchmark conjunto. "
            "Olhar: Fuzzy−Baseline −3,63 / −6,40; callout de não-significância. "
            "Não concluir: retunar Fuzzy pós-hoc com estes resultados. "
            "Ponte: Week 6 compara as quatro variantes no mesmo protocolo."
        ),
    },
    18: {
        "takeaway": "Surrogate usa 1.530 avaliações exatas — orçamento desigual, declarado, não equivalente.",
        "notes": (
            "Gancho: desenho do experimento comparativo. "
            "Olhar: tabela de avaliações; métrica 240 execuções; Surrogate 1.530 vs 15.030. "
            "Não concluir: igualdade de custo entre variantes. "
            "Ponte: convergência observada — comece por ta011."
        ),
    },
    19: {
        "takeaway": "Curvas mostram patamar e velocidade; sombra é ±1 DP entre seeds, não IC da média.",
        "replace_callout": True,
        "notes": (
            "Gancho: primeira leitura visual do Week 6. "
            "Olhar: melhor Cmax acumulado médio; Optuna para em 333 iterações. "
            "Não concluir: diferença visual = significância. "
            "Ponte: ta001 — o que muda no padrão."
        ),
    },
    20: {
        "takeaway": "Em ta001 o contraste entre variantes no patamar final é mais estreito que em ta011.",
        "replace_callout": True,
        "notes": (
            "Gancho: contraste com o slide anterior, não releitura do método. "
            "Olhar: patamares finais mais próximos; Surrogate ainda separado no custo. "
            "Não concluir: “empate visual” = ausência de efeito em todos os pares. "
            "Ponte: tabela resumo ta001."
        ),
    },
    21: {
        "takeaway": "Optuna tem melhor média/hits em ta001, mas nenhum par sobrevive a Holm.",
        "notes": (
            "Gancho: resumo por variante na instância menor. "
            "Olhar: Optuna média e 27/30 hits UB; Surrogate mais rápido e pior média. "
            "Não concluir: Optuna venceu estatisticamente em ta001. "
            "Ponte: distribuição por seed."
        ),
    },
    22: {
        "notes": (
            "Gancho: dispersão, não só a média. "
            "Olhar: espalhamento por seed; Fuzzy mais concentrado se o gráfico mostrar. "
            "Não concluir: um outlier define a variante. "
            "Ponte: mesma leitura em ta011 — o ranking descritivo muda."
        ),
    },
    23: {
        "takeaway": "Em ta011 Fuzzy lidera descritivamente; Surrogate perde qualidade de forma sustentada.",
        "notes": (
            "Gancho: contraste com ta001 — não há vencedor universal. "
            "Olhar: Fuzzy menor média/mediana/DP; 0 hits no UB 1582; Surrogate rápido e pior. "
            "Não concluir: generalizar para todo PFSP. "
            "Ponte: distribuição ta011 e depois os testes."
        ),
    },
    24: {
        "notes": (
            "Gancho: só o que muda vs ta001. "
            "Olhar: separação do Surrogate mais clara; nenhuma variante no UB. "
            "Não concluir: UB inatingível como falha do método sem contexto da instância. "
            "Ponte: Friedman + Wilcoxon + Holm."
        ),
    },
    25: {
        "takeaway": "Friedman global ≠ pares significativos; em ta011 só pares com Surrogate passam Holm.",
        "notes": (
            "Gancho: regra de leitura estatística. "
            "Olhar: Friedman rejeita nas duas; ta001 sem pares pós-Holm; ta011 Surrogate desfavorável. "
            "Não concluir: Baseline/Optuna/Fuzzy ordenados por significância. "
            "Ponte: magnitudes — tamanho de efeito, não troféu."
        ),
    },
    26: {
        "takeaway": "Magnitudes em ta011 quantificam efeito; não substituem o veredito Holm.",
        "notes": (
            "Gancho: tamanho de efeito na instância onde há sinal. "
            "Olhar: diferenças pareadas e incerteza no gráfico/tabela — direção desfavorável ao Surrogate. "
            "Não concluir: “vitória” de Fuzzy/Optuna entre si só por barra. "
            "Ponte: contraste ta001 — efeitos menores/não sustentados."
        ),
    },
    27: {
        "takeaway": "Em ta001 as magnitudes não sustentam superioridade pareada após correção.",
        "notes": (
            "Gancho: contraste com ta011, sem repetir o protocolo. "
            "Olhar: efeitos menores; alinhado à ausência de pares Holm. "
            "Não concluir: ausência de significância = identidade prática de custo. "
            "Ponte: qualidade × custo explícito."
        ),
    },
    28: {
        "takeaway": "Surrogate reduz tempo; em ta011 a perda de qualidade é o preço estatisticamente sustentado.",
        "replace_callout": True,
        "notes": (
            "Gancho: RQ3 em uma frase. "
            "Olhar: eixo qualidade vs tempo/avaliações; Surrogate no canto rápido. "
            "Não concluir: velocidade = equivalência de solução. "
            "Ponte: Colab — integridade, não novo ranking."
        ),
    },
    29: {
        "takeaway": "Reprodução Colab audita integridade operacional; não cria resultado científico novo.",
        "notes": (
            "Gancho: ameaça de reprodutibilidade. "
            "Olhar: os quatro cards — o que bateu / o que ficou limitado. "
            "Não concluir: ambiente diferente invalida Week 6 sem evidência concreta. "
            "Ponte: síntese do estudo principal e fechamento do Núcleo."
        ),
    },
    30: {
        "takeaway": "Núcleo fechado: RQ1 corrigida; RQ2 sem vencedor universal; RQ3 com trade-off explícito.",
        "notes": (
            "Gancho: feche o estudo principal antes das extensões. "
            "Olhar: tabela etapa→conclusão defensável alinhada a RQ1–3. "
            "Não concluir: extensões já resolvidas. "
            "Ponte: Extensão 1 — investigação aberta sobre o surrogate."
        ),
    },
    31: {
        "takeaway": "Extensão: mais rótulos melhoram predição global? Isto não substitui o Week 6.",
        "notes": (
            "Gancho: fronteira de ato — daqui em diante é extensão. "
            "Olhar: pergunta da curva v2; instâncias maiores ta071/ta111. "
            "Não concluir: resultado da curva como qualidade do GWO Week 6. "
            "Ponte: números em N=32k."
        ),
    },
    32: {
        "takeaway": "Em ta071, N=32k melhora ajuste/ranking; utilidade top-k permanece a pergunta aberta.",
        "replace_callout": True,
        "notes": (
            "Gancho: mensagem 1 — mais dados ajudam o ajuste. "
            "Olhar: métricas em N=32k na tabela/callout. "
            "Não concluir: top-k resolvido. "
            "Ponte: ta111 — a instância maior estressa mais."
        ),
    },
    33: {
        "takeaway": "ta111 é mais difícil: ganhos existem, mas o nível absoluto de ranking/erro continua limitado.",
        "replace_callout": True,
        "notes": (
            "Gancho: contraste com ta071, não repetir o protocolo. "
            "Olhar: nível de Spearman/RMSE vs slide anterior. "
            "Não concluir: mesma utilidade operacional nas duas escalas. "
            "Ponte: ganhos 4k→32k e limites."
        ),
    },
    34: {
        "takeaway": "De 4k a 32k o erro cai e o ranking sobe; recuperar os melhores candidatos continua fraco.",
        "notes": (
            "Gancho: três mensagens da extensão em um slide. "
            "Olhar: ganhos reportados; limites explícitos na tabela. "
            "Não concluir: escalar N resolve seleção top-k. "
            "Ponte: gráficos — Spearman primeiro."
        ),
    },
    35: {
        "takeaway": "Mensagem 1/3: Spearman sobe com N em ta111, com variabilidade entre repetições.",
        "replace_callout": True,
        "notes": (
            "Gancho: evidência visual da mensagem 1. "
            "Olhar: tendência 4k→32k e faixa entre reps. "
            "Não concluir: IC sobre novos testes/instâncias. "
            "Ponte: top-10 — a mensagem que não acompanha o Spearman."
        ),
    },
    36: {
        "takeaway": "Mensagem 2/3: em ta111 o ranking global não se traduz em recuperação top-10 útil.",
        "replace_callout": True,
        "notes": (
            "Gancho: utilidade operacional vs métrica global. "
            "Olhar: recall/regret top-10 no gráfico; Surrogate já existe na Week 6 — aqui avalia-se a qualidade de seleção do modelo. "
            "Não concluir: “não integrar surrogate ao GWO” — a variante já está no núcleo; a questão é se o modelo prioriza bem. "
            "Ponte: RMSE completa o trio em ta111."
        ),
    },
    37: {
        "takeaway": "RMSE cai com N em ta111; ganho preditivo global ≠ ganho de seleção.",
        "replace_callout": True,
        "notes": (
            "Gancho: fechar ta111 com a métrica de erro. "
            "Olhar: queda de RMSE ao longo de N. "
            "Não concluir: erro menor autoriza declarar top-k resolvido. "
            "Ponte: mesma trinca em ta071 — contraste de escala."
        ),
    },
    38: {
        "takeaway": "Em ta071 o Spearman também sobe com N — mesmo padrão, escala diferente.",
        "replace_callout": True,
        "notes": (
            "Gancho: contraste ta071 vs ta111, sem repetir o método. "
            "Olhar: curva Spearman; nível absoluto vs slide 35. "
            "Não concluir: transferir recalls de ta111 para ta071. "
            "Ponte: top-10 em ta071 (recalls próprios desta instância)."
        ),
    },
    39: {
        "takeaway": "Mensagem 3/3: instância importa — top-10 em ta071 não copia o diagnóstico de ta111.",
        "replace_callout": True,
        "notes": (
            "Gancho: contraste operacional entre escalas. "
            "Olhar: recalls/regret deste slide (ta071), não os de ta111. "
            "Não concluir: um único N ou instância fecha a extensão. "
            "Ponte: RMSE ta071 e depois comparação de modelos."
        ),
    },
    40: {
        "takeaway": "RMSE em ta071 confirma mensagem 1; mensagens 2–3 seguem nos slides de seleção.",
        "replace_callout": True,
        "notes": (
            "Gancho: último gráfico da trinca ta071. "
            "Olhar: tendência de RMSE com N. "
            "Não concluir: reiniciar a aula do método — vá à comparação de modelos. "
            "Ponte: piloto de quatro regressores, uma célula."
        ),
    },
    41: {
        "takeaway": "Piloto exploratório: uma célula (ta111, N=8k, 1 rep) — não é a matriz de 80 ajustes.",
        "replace_callout": True,
        "notes": (
            "Gancho: comparação de arquiteturas sob dados idênticos. "
            "Olhar: escopo do piloto no kicker/callout. "
            "Não concluir: vencedor confirmatório. "
            "Ponte: leitura — RMSE vs top-k."
        ),
    },
    42: {
        "takeaway": "Melhor erro global no piloto não melhorou a recuperação dos melhores schedules.",
        "replace_callout": True,
        "notes": (
            "Gancho: decisão A2 em miniatura. "
            "Olhar: Spearman/RMSE vs recall top-10 0% e regrets; tempos de treino. "
            "Não concluir: trocar o MLP da Week 6 só com esta célula. "
            "Ponte: distribuição real de candidatos GWO."
        ),
    },
    43: {
        "takeaway": "300.600 linhas na mesma trajetória não são 300.600 instâncias independentes.",
        "notes": (
            "Gancho: hipótese de mismatch distribuição uniforme vs busca. "
            "Olhar: 20 execuções; CSV ~551 MB fora do Git; proveniência Cost Pilot v2. "
            "Não concluir: caracterização completa já feita. "
            "Ponte: Extensão 2 — meta-learning é outro problema."
        ),
    },
    44: {
        "takeaway": "Surrogate prediz Cmax de uma permutação; meta-learning escolhe a variante por instância.",
        "notes": (
            "Gancho: fronteira conceitual obrigatória. "
            "Olhar: split Surrogate vs Meta — entradas/saídas diferentes. "
            "Não concluir: misturar datasets ou usar a curva como prova de seletor. "
            "Ponte: piloto 36 e checkpoint 60."
        ),
    },
    45: {
        "takeaway": "Checkpoint 60: Fuzzy 20/48; holdout selado; RF no piloto ≈ sempre Fuzzy.",
        "notes": (
            "Gancho: estado exploratório do seletor. "
            "Olhar: 576/576; vitórias; low-confidence 30/48; holdout não executado. "
            "Não concluir: meta-learner pronto para produção. "
            "Ponte: próximos gates sem abrir holdout."
        ),
    },
    46: {
        "takeaway": "Decisão 60→120 usa só desenvolvimento/custo/integridade — holdout permanece fechado.",
        "notes": (
            "Gancho: o que falta antes de qualquer alegação confirmatória. "
            "Olhar: quatro gates — decisão, coleta, freeze, holdout único. "
            "Não concluir: executar holdout agora. "
            "Ponte: ameaças à validade do estudo completo."
        ),
    },
    47: {
        "takeaway": "Ameaça externa mais forte: só ta001 e ta011 no núcleo; orçamento Surrogate desigual.",
        "notes": (
            "Gancho: limites na ordem de força. "
            "Olhar: lista — externa (2 instâncias), interna (bug/orçamento), construção top-k, meta holdout. "
            "Não concluir: esconder limitações. "
            "Ponte: respostas às RQs na mesma linguagem da abertura."
        ),
    },
    48: {
        "takeaway": "RQ1: v1 inválida e corrigida. RQ2: sem vencedor universal. RQ3: Surrogate rápido com perda em ta011.",
        "notes": (
            "Gancho: responder as perguntas do slide 02. "
            "Olhar: quatro blocos RQ1/RQ2/RQ3/Extensões. "
            "Não concluir: extensões confirmatórias. "
            "Ponte: decisões em aberto para discussão com o professor."
        ),
    },
    49: {
        "takeaway": "Discuta prioridades: matriz de modelos, distribuição GWO, decisão 60→120, escopo da extensão.",
        "notes": (
            "Gancho: agenda, não promessa. "
            "Olhar: quatro bullets como perguntas ao professor. "
            "Não concluir: tudo já está no cronograma obrigatório. "
            "Ponte: apêndice só se pedirem fórmulas, stats, artefatos ou bibliografia."
        ),
    },
    50: {
        "notes": (
            "BACKUP Q&A. Só abra se perguntarem orçamento ou referências-base. "
            "Olhar: N_eval e os três orçamentos; Taillard/Mirjalili. "
            "Não ler o slide inteiro. "
            "Ponte: volte ao fio ou ao próximo apêndice pedido."
        ),
        "takeaway": "Apêndice de consulta — não faz parte do fio oral principal.",
    },
    51: {
        "notes": (
            "BACKUP Q&A. "
            "Olhar: papel de Friedman / Wilcoxon / Holm e o cuidado de cada um. "
            "Não concluir: IC da curva cobre novos conjuntos de teste. "
            "Ponte: volte às conclusões se a pergunta acabou."
        ),
        "takeaway": "Use só se perguntarem como defender os testes.",
    },
    52: {
        "notes": (
            "BACKUP Q&A. "
            "Olhar: caminho do artefato pedido (Week 6, curva, meta, runbook). "
            "Não improvisar hashes de memória — aponte o arquivo. "
            "Ponte: proveniência com HEAD se pedirem rastreabilidade."
        ),
        "takeaway": "Mapa de evidências para auditoria sob demanda.",
    },
    53: {
        "takeaway": "Branch recovery/surrogate-learning-curve-v2-oom • HEAD 8c276c9… — atualizar se o commit mudar.",
        "notes": (
            "BACKUP Q&A. "
            "Olhar: tabela evidência→artefato; rodapé com branch/HEAD. "
            "Não alegar populations.csv integral versionado. "
            "Ponte: referências bibliográficas se pedirem DOI."
        ),
    },
    54: {
        "notes": (
            "BACKUP Q&A. Não ler em voz alta. "
            "Olhar: item pedido (Mirjalili, Taillard, Optuna, Mamdani, testes, Smith-Miles). "
            "Não transformar em aula bibliográfica. "
            "Ponte: encerre ou volte à pergunta do professor."
        ),
        "takeaway": "Lista de consulta — cite sob demanda; resultados vêm dos artefatos do repositório.",
    },
}
