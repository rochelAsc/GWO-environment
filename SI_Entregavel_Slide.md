

Grey Wolf Optimizer (GWO) Aplicação na Predição de Notificações de Dengue 



Rochel Santos 

Sistemas Inteligentes 

Semana 1 – 20 de outubro de 2026 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 1 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Sumário 

> 1 Introdução 

> 2 Inspiração Biológica 

> 3 Formulação Matemática 

> 4 Variáveis Críticas de Estado 

- 5 Mapeamento de Entradas e Saídas 

> 6 Aplicação em Dengue 

> 7 Considerações Finais 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 2 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Introdução 











Algoritmos bioinspirados simulam comportamentos naturais para resolver problemas de otimização. 

O **Grey Wolf Optimizer (GWO)** foi proposto por Mirjalili et al. (2014). Inspirado na hierarquia social e na caça cooperativa do lobo cinzento ( _Canis lupus_ ). 

Vantagens: poucos parâmetros, sem derivadas, fácil implementação e bom equilíbrio exploração-extração. 

**Aplicação proposta** : otimizar hiperparâmetros de modelos preditivos de notificações de dengue. 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>3 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

<mark>Semana 1 – 20 de outubro de 2026</mark> 

Hierarquia Social da Matilha 









**Alpha (** _α_ **)** : líder; toma decisões de caça, descanso e vigília. **Beta (** _β_ **)** : subordinado ao alpha; auxilia na decisão e impõe disciplina. **Delta (** _δ_ **)** : papéis específicos (batedores, sentinelas, caçadores, cuidadores). **Omega (** _ω_ **)** : último nível; mantém a estrutura de dominância. 

### Tradução para o algoritmo 





As três melhores soluções ( _α_ , _β_ , _δ_ ) guiam a busca; os demais lobos ( _ω_ ) seguem. 



<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 4 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Etapas da Caça 

> 1 **Rastreamento e aproximação** da presa. 

> 2 **Cerco** à presa. 

> 3 **Ataque** quando a presa para de se mover. 

O GWO modela matematicamente cada etapa por meio de vetores de posição e coeficientes adaptativos. 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 5 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Cerco à Presa 

Distância entre lobo e presa: 



<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 6 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

## Caça (Liderança por _α_ , _β_ e _δ_ ) 

Distâncias aos três melhores: 



<!-- Start of picture text -->
Dα =<br>��� ⃗C 1  ·⃗ Xα −⃗ X ���<br>Dβ =<br>��� ⃗C 2  ·⃗ Xβ −⃗ X ���<br>Dδ =<br>��� ⃗C 3  ·⃗ Xδ −⃗ X ���<br><!-- End of picture text -->

Posições intermediárias: 



Posição final: 

_X_ ( _t_ + 1) = _⃗_<sup>_X_1 +</sup><sup>_⃗X_2 +</sup><sup>_⃗X_3</sup> (4) 3 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 7 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Exploração vs. Extração 









- _|⃗A| ≥_ 1: lobos se afastam da presa _→_ **exploração** (busca global). 

- _|⃗A| <_ 1: lobos se aproximam da presa _→_ **extração** (refinamento). 

- _C⃗_ introduz aleatoriedade e ajuda a manter a diversidade. 

- _⃗a_ decai de 2 a 0, reduzindo gradualmente a exploração. 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 8 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Variáveis Críticas 



**Diversidade populacional** : dispersão das posições dos lobos. Alta diversidade evita ótimos locais. 



**Taxa de convergência** : velocidade de aproximação do ótimo; controlada pelo decaimento de _⃗ a_ . 



**Balanceamento exploração/explotacão** : controlado por _⃗ A_ e _⃗ C_ . 

### Monitoramento 





Acompanhar a evolução do fitness médio e do desvio padrão ao longo das iterações. 



<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 9 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

## Pseudocódigo do GWO 

> 1 Inicializar população _⃗ Xi_ ( _i_ = 1 _, . . . , N_ ), _a_ = 2, _A_ , _C_ . 

> 2 Avaliar fitness de cada lobo. 

> 3 Definir _α_ , _β_ , _δ_ (melhores soluções). 

> 4 **Enquanto** _t < T_ max: Atualizar _a_ , _A_ , _C_ . Para cada lobo: atualizar posição via Eqs. de cerco e caça. Aplicar limites [ _lb, ub_ ]. Avaliar fitness. Atualizar _α_ , _β_ , _δ_ . 

> 5 **Retornar** _⃗ Xα_ . 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 10 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

# Representação dos Indivíduos <mark>nn</mark> 



Cada lobo _i_ é um vetor _D_ -dimensional: _Xi_ = ( _xi,_ 1 _, xi,_ 2 _, . . . , xi,D_ ) 







População: matriz _N × D_ (N lobos, D dimensões). **Entradas** : _N_ , _T_ max, limites _lb_ e _ub_ , função de fitness. **Saída** : posição do lobo _α_ ( _X⃗ α_ ) ao final das iterações. 

### Inicialização 





<!-- Start of picture text -->
X⃗ i = ⃗ lb  + rand(0 ,  1)  ⊙ ( ⃗ub −⃗ lb )<br><!-- End of picture text -->

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 11 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

## Função de Aptidão e Espaço de Busca 

**Função de aptidão** (minimização do erro de previsão): 



<!-- Start of picture text -->
�<br>� 1 T<br>f  ( ⃗X ) = RMSE = � T �( yt − y ˆ t ) 2<br>� t =1<br><!-- End of picture text -->

**Espaço de busca** : hiperparâmetros de uma LSTM. 



<!-- Start of picture text -->
Hiperparâmetro Mínimo Máximo Tipo<br>Taxa de aprendizado 10 − 5 10 − 1 Contínuo (log)<br>Nž de camadas LSTM 1 4 Inteiro<br>Unidades por camada 16 256 Inteiro<br>Tamanho da janela 7 90 Inteiro<br>Taxa de dropout 0.0 0.5 Contínuo<br><!-- End of picture text -->

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 12 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Integração GWO + Modelo Preditivo 

GWO gera configuração de hiperparâmetros _↓_ Treina modelo LSTM _↓_ 

Avalia RMSE no conjunto de validação _↓_ 

RMSE retorna como fitness do lobo _↓_ Atualiza _α_ , _β_ , _δ_ e posições _↓_ 

Repete até _T_ max _↓_ 

Retorna melhor configuração ( _X⃗ α_ ) 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 13 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Considerações Finais 





O GWO é simples, robusto e adequado para otimização de hiperparâmetros. A aplicação à problemas que envolvem predição de variáveis e informações, permite implementar ajuste de modelos de séries temporais. 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 14 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

Referências 

beamericonarticle.pdfMIRJALILI, S.; MIRJALILI, S. M.; LEWIS, A. Grey Wolf Optimizer. _Advances in Engineering Software_ , v. 69, p. 46–61, 2014. beamericonarticle.pdfCHOUDHARY, V. et al. Grey Wolf Optimizer: A review. _MethodsX_ , v. 12, 102747, 2024. 

beamericonarticle.pdfBOUCHIBA, K.; BADIS, L. Gray Wolf Optimization for CNN hyperparameter tuning. Université de Bouira, 2023. 

<mark>Rochel Santos (Sistemas Inteligentes)</mark> 

<mark>Semana 1 – 20 de outubro de 2026 15 / 15</mark> 

<mark>Solver Bioinspirado</mark> 

