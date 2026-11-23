# Revisão da Semana 1 — Fundamentação do Grey Wolf Optimizer

- **Data:** 2026-11-23
- **Escopo:** inspiração bioinspirada, formulação matemática, representação, entradas/saídas, fitness e espaço de busca.
- **Status:** entregáveis da Semana 1 localizados e inspecionados; revisão técnica do material original e da transição de aplicação em andamento.
- **Preservação:** documento aditivo; nenhum artefato histórico foi sobrescrito.

## 1. Exigências do roteiro

A Semana 1 exige pesquisa de um solver bioinspirado, análise dos mecanismos que o inspiram, identificação de variáveis críticas de estado, apresentação em PDF e documento de aproximadamente duas páginas com formulação matemática, entradas/saídas, representação dos indivíduos, fitness e espaço de busca.

O algoritmo escolhido no projeto é o Grey Wolf Optimizer (GWO), de Mirjalili, Mirjalili e Lewis (2014).

## 2. Fundamentação

O GWO é uma metaheurística populacional inspirada na hierarquia social e no comportamento de caça dos lobos-cinzentos. A abstração computacional usa:

- **Alpha (α):** melhor solução;
- **Beta (β):** segunda melhor solução;
- **Delta (δ):** terceira melhor solução;
- **Omega (ω):** demais soluções, guiadas pelas três líderes.

Os mecanismos modelados são cercamento da presa, caça guiada e ataque/aproximação. A presa representa a região da solução ótima, desconhecida durante a otimização. A inspiração biológica é uma metáfora de projeto, não uma reprodução literal da ecologia de uma matilha.

## 3. Formulação matemática

Considere (N) lobos em um espaço de dimensão (D). A posição do lobo (i) na iteração (t) é (\mathbf{X}_i(t)\).

### 3.1 Cercamento

\[
\mathbf{D}=|\mathbf{C}\odot\mathbf{X}_p(t)-\mathbf{X}(t)|,
\qquad
\mathbf{X}(t+1)=\mathbf{X}_p(t)-\mathbf{A}\odot\mathbf{D}.
\]

Os coeficientes são:

\[
\mathbf{A}=2a\mathbf{r}_1-a,
\qquad
\mathbf{C}=2\mathbf{r}_2,
\]

em que os componentes de \(\mathbf{r}_1\) e \(\mathbf{r}_2\) são amostrados em [0,1], independentemente. \(\odot\) indica produto coordenada a coordenada.

### 3.2 Caça guiada por três líderes

Como a presa não é conhecida, as três melhores soluções orientam a população:

\[
\mathbf{D}_{\alpha}=|\mathbf{C}_1\odot\mathbf{X}_{\alpha}-\mathbf{X}|,
\quad
\mathbf{D}_{\beta}=|\mathbf{C}_2\odot\mathbf{X}_{\beta}-\mathbf{X}|,
\quad
\mathbf{D}_{\delta}=|\mathbf{C}_3\odot\mathbf{X}_{\delta}-\mathbf{X}|.
\]

\[
\mathbf{X}_1=\mathbf{X}_{\alpha}-\mathbf{A}_1\odot\mathbf{D}_{\alpha},
\quad
\mathbf{X}_2=\mathbf{X}_{\beta}-\mathbf{A}_2\odot\mathbf{D}_{\beta},
\quad
\mathbf{X}_3=\mathbf{X}_{\delta}-\mathbf{A}_3\odot\mathbf{D}_{\delta}.
\]

A posição seguinte é a média das três estimativas:

\[
\boxed{\mathbf{X}(t+1)=\frac{\mathbf{X}_1+\mathbf{X}_2+\mathbf{X}_3}{3}}.
\]

Na versão canônica, `a` decresce linearmente de 2 para 0. Quando \(|A|>1\), os movimentos podem favorecer exploração; quando \(|A|<1\), tendem a favorecer explotação ao redor dos líderes. Como `A` é vetorial, essa interpretação ocorre por coordenada. O schedule não garante encontrar o ótimo global.

## 4. Aplicação ao PFS do projeto

O motor legado representa um Permutation Flow Shop (PFS) de uma fábrica: todos os jobs percorrem as máquinas na mesma ordem e compartilham uma permutação.

Para `n` jobs, cada lobo é um vetor de chaves contínuas:

\[
\mathbf{X}_i\in[0,1]^n,\qquad D=n.
\]

A permutação é obtida ordenando as chaves:

\[
\pi_i=\operatorname{argsort}(\mathbf{X}_i).
\]

Valores menores recebem prioridade anterior. Essa é uma representação *random keys*. Um relatório histórico chama o decoder de “Bucket Sort Decode”, mas o código examinado utiliza `numpy.argsort`, não um algoritmo literal de bucket sort. Chaves diferentes podem produzir a mesma permutação; empates precisam de regra explícita de desempate em uma implementação nova.

### 4.1 Cálculo do Total Tardiness

Para o job na posição (r), na máquina (k):

\[
C_{\pi(r),k}=\max(C_{\pi(r-1),k},C_{\pi(r),k-1})+p_{\pi(r),k},
\]

com tempos de fronteira iguais a zero. O tardiness do job (j) é:

\[
T_j=\max(0,C_{j,m}-d_j).
\]

A função objetivo minimizada é:

\[
\boxed{TT(\pi)=\sum_{j=1}^{n}\max(0,C_{j,m}-d_j)}.
\]

Logo, a aptidão de um lobo no PFS é (f(\mathbf{X}_i)=TT(\operatorname{argsort}(\mathbf{X}_i))). Menor valor é melhor.

## 5. Mapeamento de entradas, saídas e estado

| Elemento | Definição no PFS |
|---|---|
| Entradas | Matriz de tempos de processamento, datas de entrega e dimensões |
| Parâmetros | Número de lobos, limite de iterações/avaliações, seed, limites e schedule de (a) |
| Indivíduo | Vetor de (n) chaves em [0,1] |
| Decoder | Ordenação das chaves em uma permutação |
| Fitness | Total Tardiness |
| Estado | Posições, aptidões, líderes α/β/δ e parâmetro (a) |
| Saída | Melhor permutação, tardiness e histórico de convergência |

Diversidade populacional e estagnação não são variáveis obrigatórias do GWO canônico. No projeto, são usadas como entradas do Fuzzy: diversidade é medida pela dispersão das coordenadas e estagnação pelo número de gerações sem melhoria. A escala, normalização e regras dessas variáveis devem ser auditadas na Semana 5.

## 6. Diferenças confirmadas entre teoria e código

1. O GWO contínuo foi implementado do zero e recebe uma função objetivo genérica.
2. No PFS, o vetor tem dimensão (n), é decodificado por `argsort` e a mesma permutação é aplicada a todas as máquinas.
3. O objetivo é minimizar Total Tardiness calculado pelo motor PFS.
4. O GWO legado atualiza lobos e líderes sequencialmente/in-place. Lobos posteriores podem usar líderes já alterados na mesma geração. Isso deve ser descrito como característica da implementação, não escondido sob uma descrição genérica de atualização síncrona.
5. O schedule legado chamado `exponential` calcula (a(t)=2(1-(t/T)^2)), que é quadrático, não exponencial. Novos experimentos devem usar o nome `quadratic`; os dados antigos mantêm o nome original com ressalva.
6. A população inicial também é avaliada. Com `N` lobos e `T` iterações completas, o legado realiza `N(T+1)` avaliações.
7. O GWO random-key para DPFSP-DD é outro algoritmo aplicado a outro problema: usa (2n) chaves, codifica atribuição de fábricas e prioridades e atualiza a população sincronamente. Não confundir com o PFS.

## 7. Materiais originais da Semana 1

Foram localizados e lidos os dois arquivos adicionados à raiz do repositório:

- `SI_Entregavel.md`: documento de formulação matemática e mapeamento do GWO, com três páginas extraídas. Apresenta hierarquia, etapas da caça, variáveis críticas, equações, representação, entradas/saídas, RMSE e espaço de busca de uma LSTM.
- `SI_Entregavel_Slide.md`: conteúdo de uma apresentação de 15 slides, datada de 20 de outubro de 2026, com introdução, inspiração biológica, formulação, pseudocódigo, representação, fitness, integração GWO+LSTM e referências.

Os arquivos comprovam que os entregáveis documentais da Semana 1 foram produzidos e estão versionados. A extração textual apresenta lacunas nas equações e elementos gráficos; para validar a qualidade visual e matemática dos PDFs originais, seria necessário inspecionar os arquivos renderizados, não apenas o Markdown convertido.

### Mudança de aplicação

Os materiais originais descrevem GWO para otimizar hiperparâmetros de uma LSTM na predição de notificações de dengue, com RMSE como fitness. O projeto atualmente auditado aplica GWO a problemas de sequenciamento de produção (PFS e DPFSP-DD), com Total Tardiness no PFS. Portanto, há uma mudança clara de domínio, representação e função objetivo. A fundamentação matemática do GWO é reaproveitável, mas a aplicação à dengue não deve ser apresentada como se fosse a aplicação experimental final do repositório. A cronologia e a justificativa da mudança precisam ser recuperadas dos registros/relatórios do trabalho.

## 8. Checklist da Semana 1

| Exigência | Evidência | Situação |
|---|---|---|
| Escolha do solver | Notebook/export identifica GWO e cita Mirjalili et al. (2014) | Atendido |
| Inspiração e hierarquia | Referência primária e código identificados; explicação acadêmica precisa ser consolidada | Parcial |
| Formulação matemática | Equações registradas nesta revisão | Revisado |
| Entradas, saídas e representação | Mapeamento PFS registrado nesta revisão | Revisado |
| Fitness e espaço de busca | Random keys, domínio e Total Tardiness confirmados no código | Atendido tecnicamente |
| Variáveis críticas de estado | Líderes, posições e (a) identificados; diversidade/estagnação são extensões Fuzzy | Parcial |
| Documento de formulação | `SI_Entregavel.md` | Localizado; conteúdo inspecionado |
| Apresentação | `SI_Entregavel_Slide.md` (15 slides) | Localizada; conteúdo inspecionado |
| Correspondência com a aplicação final | Materiais usam LSTM/dengue; projeto atual usa PFS/DPFSP-DD | Mudança de escopo a documentar |

## 9. Pendências da revisão da Semana 1

- Conferir visualmente os PDFs originais correspondentes, se disponíveis, pois o Markdown convertido perdeu partes de equações e imagens.
- Documentar a transição da proposta LSTM/dengue para PFS/DPFSP-DD, sem apagar os materiais originais.
- Separar claramente a formulação canônica do GWO das adaptações específicas do PFS e do DPFSP-DD.
- Explicitar que diversidade e estagnação são entradas do Fuzzy, não variáveis nativas do GWO.

## 10. Referência primária

MIRJALILI, S.; MIRJALILI, S. M.; LEWIS, A. Grey Wolf Optimizer. *Advances in Engineering Software*, v. 69, p. 46–61, 2014. DOI: [10.1016/j.advengsoft.2013.12.007](https://doi.org/10.1016/j.advengsoft.2013.12.007).

## 11. Fontes internas examinadas

- `sistemas_inteligentes_roteiro (1).md`
- `scripts/sistemas_inteligentes_entregavel.py`
- `scripts/legacy_pfs.py`
- `scripts/discrete_gwo_dpfsp.py`
- `docs/audits/2026-11-22-legacy-gwo-dynamics.md`
- `docs/audits/2026-11-22-initial-code-audit.md`
- `docs/roadmap_alignment.md`

**Limite:** revisão baseada em inspeção estática do código e na formulação publicada. Não é uma nova execução experimental e não comprova, por si só, a entrega acadêmica original da Semana 1.
