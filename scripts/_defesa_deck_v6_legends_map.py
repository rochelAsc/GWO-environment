"""Per-slide legends and short clarifying text for defesa deck v6."""
from __future__ import annotations

# slide_index -> {
#   legend: list[(sym, meaning)],  # required if present
#   compact: bool,
#   extra_after: "equation_small" | "mathgrid" | "first_table" | "table_pair" | "chart" | "split" | None
#   extra_html: str,  # inserted after the anchor
#   note_append: str | None,  # optional short append to speaker notes
# }

LEGENDS: dict[int, dict] = {
    4: {
        "legend": [
            ("π", "permutação dos jobs"),
            ("n, m", "jobs e máquinas"),
            ("p<sub>ij</sub>", "tempo do job i na máquina j"),
            ("C<sub>max</sub>", "makespan (conclusão final)"),
            ("C<sub>πk,j</sub>", "conclusão do k-ésimo job na máquina j"),
            ("UB", "upper bound publicado (não ótimo provado)"),
        ],
        "compact": True,
        "extra_after": "equation_small",
        "extra_html": (
            '<p class="clarify">Um job só começa na máquina j depois de terminar em j−1 '
            "e a máquina j estar livre.</p>"
        ),
        "note_append": " Olhar também: legenda de símbolos no rodapé.",
    },
    5: {
        "legend": [
            ("x", "random keys em [0,1]<sup>n</sup>"),
            ("argsort", "ordena chaves → permutação π"),
            ("α, β, δ", "três melhores (líderes)"),
            ("C<sub>max</sub>(π)", "makespan exato decodificado"),
        ],
        "compact": True,
    },
    6: {
        "legend": [
            ("a", "amplitude exploração→explotação"),
            ("A, C", "coeficientes aleatórios GWO"),
            ("r₁, r₂", "U(0,1) por dimensão"),
            ("⊙", "produto elemento a elemento"),
            ("X<sub>α</sub>", "líder alpha (idem β, δ)"),
            ("X<sub>i</sub>(t+1)", "nova posição = média X₁,X₂,X₃"),
        ],
        "extra_after": "mathgrid",
        "extra_html": (
            '<p class="clarify">⊙ = produto elemento a elemento; a nova posição é a média '
            "das três atrações aos líderes, depois limitada a [0,1].</p>"
        ),
        "note_append": " Olhar também: legenda no rodapé.",
    },
    12: {
        "legend": [
            ("RMSE", "erro quadrático médio (escala do makespan)"),
            ("MAE", "erro absoluto médio"),
            ("R²", "fração da variância explicada (1 = ajuste perfeito)"),
            ("Spearman ρ", "correlação de postos — qualidade do ranking"),
        ],
        "extra_after": "first_table",
        "extra_html": (
            '<p class="clarify">Erro absoluto baixo ≠ boa ordenação dos melhores candidatos.</p>'
        ),
        "compact": True,
    },
    14: {
        "legend": [
            ("D", "diversidade média no espaço de random keys"),
            ("S", "estagnação normalizada (sem melhoria / janela 20)"),
            ("a(t)", "agenda de exploração; Fuzzy multiplica a base linear"),
            ("Mamdani", "inferência fuzzy por regras (min/max) + centroide"),
        ],
        "compact": True,
    },
    18: {
        "legend": [
            ("Aval. exatas", "cálculos reais de makespan por run"),
            ("Predições", "consultas ao surrogate (não atualizam líderes sozinhas)"),
            ("1.530 vs 15.030", "Surrogate reavalia só top-3 por geração — orçamento desigual"),
        ],
        "compact": True,
    },
    25: {
        "legend": [
            ("Friedman", "teste global: as 4 variantes diferem nos blocos de seed?"),
            ("Wilcoxon", "comparação pareada por par de variantes"),
            ("Holm", "correção da multiplicidade das 6 comparações"),
            ("χ² / p", "estatística do Friedman e evidência contra igualdade"),
        ],
        "extra_after": "table_pair",
        "extra_html": (
            '<p class="clarify">Rejeitar igualdade global não identifica qual par difere — '
            "isso fica com Wilcoxon + Holm.</p>"
        ),
        "compact": True,
    },
    31: {
        "legend": [
            ("LHS", "Latin Hypercube — amostragem espacial de random keys"),
            ("N", "nº de permutações de treino por ajuste"),
            ("uniforme", "amostra de permutações uniformes (controle)"),
        ],
        "compact": True,
    },
    32: {
        "legend": [
            ("N=32k", "32.000 permutações de treino"),
            ("Spearman", "qualidade do ranking previsto"),
            ("RMSE", "erro médio na escala do makespan"),
            ("LHS / uniforme", "dois métodos de amostragem no mesmo protocolo"),
        ],
        "compact": True,
    },
    33: {
        "legend": [
            ("ta111", "instância 500×20 — escala maior que ta071"),
            ("Spearman / RMSE", "ranking vs erro absoluto no teste fixo"),
            ("N=32k", "mesmo teto de amostra da curva v2"),
        ],
        "compact": True,
    },
    34: {
        "legend": [
            ("4k → 32k", "faixa de tamanhos da curva v2"),
            ("5 reps", "repetições com seeds do protocolo"),
            ("top-k", "recuperar os k melhores makespans do teste"),
        ],
        "compact": True,
    },
    35: {
        "legend": [
            ("Spearman ρ", "correlação de postos (↑ melhor)"),
            ("N", "tamanho do treino no eixo"),
            ("faixa", "dispersão entre as 5 repetições"),
        ],
        "compact": True,
    },
    36: {
        "legend": [
            ("recall top-10", "fração dos 10 melhores reais entre os 10 previstos"),
            ("regret", "gap do melhor selecionado vs melhor real do teste"),
            ("↑ ranking ≠ ↑ top-k", "Spearman alto não garante recuperar os melhores"),
        ],
        "extra_after": "chart",
        "extra_html": (
            '<p class="clarify">Ranking global ≠ recuperar os k melhores schedules.</p>'
        ),
        "compact": True,
    },
    37: {
        "legend": [
            ("RMSE", "erro quadrático médio no teste fixo (↓ melhor)"),
            ("N", "tamanho do treino"),
            ("faixa", "variação entre repetições"),
        ],
        "compact": True,
    },
    38: {
        "legend": [
            ("Spearman ρ", "ranking em ta071 (escala menor que ta111)"),
            ("N", "tamanho do treino"),
            ("contraste", "mesmo protocolo; nível absoluto diferente de ta111"),
        ],
        "compact": True,
    },
    39: {
        "legend": [
            ("recall top-10", "recuperação dos 10 melhores em ta071"),
            ("regret", "gap do melhor previsto vs melhor real"),
            ("ta071 ≠ ta111", "não copiar recalls entre instâncias"),
        ],
        "extra_after": "chart",
        "extra_html": (
            '<p class="clarify">Ranking global ≠ recuperar os k melhores schedules.</p>'
        ),
        "compact": True,
    },
    40: {
        "legend": [
            ("RMSE", "erro em ta071 ao longo de N"),
            ("↓ melhor", "menor RMSE = melhor ajuste absoluto"),
        ],
        "compact": True,
    },
    42: {
        "legend": [
            ("recall top-10", "interseção com os 10 melhores reais / 10"),
            ("regret top-10", "best-selected: min(y escolhido) − min(y teste)"),
            ("Spearman / RMSE", "ranking global e erro — métricas distintas da seleção"),
        ],
        "compact": True,
    },
    44: {
        "legend": [
            ("permutação", "entrada do surrogate → estima C<sub>max</sub>"),
            ("instância", "unidade do meta-learning → escolhe variante GWO"),
            ("matriz P", "tempos de processamento; origem das features meta"),
        ],
        "extra_after": "split",
        "extra_html": (
            '<p class="clarify">Não misture os dois problemas: prever makespan ≠ escolher algoritmo.</p>'
        ),
        "compact": True,
    },
    50: {
        "legend": [
            ("N<sub>eval</sub>", "avaliações exatas por execução"),
            ("N<sub>wolves</sub>", "tamanho da população"),
            ("T", "nº de iterações (gerações após a inicial)"),
            ("T+1", "inclui a avaliação da população inicial"),
        ],
        "compact": True,
    },
    51: {
        "legend": [
            ("Friedman", "teste global em blocos de seed"),
            ("Wilcoxon", "pares de variantes"),
            ("Holm", "controle de erro nas múltiplas comparações"),
            ("IC curva", "variação entre reps — condicionado ao teste fixo"),
        ],
        "compact": True,
    },
}

LEGEND_CSS = """
.legend{
  margin:4px 0 0;padding:4px 8px 2px;border-top:1px solid var(--line);
  font-size:clamp(9px,1vw,11px);line-height:1.28;color:var(--muted);
}
.legend>b{
  display:block;font-size:9px;letter-spacing:1.1px;text-transform:uppercase;
  color:var(--accent);font-weight:700;margin:0 0 2px;font-family:var(--sans);
}
.legend ul{
  list-style:none;margin:0;padding:0;
  display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px 12px;
}
.legend.compact ul{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.legend li{margin:1px 0;padding:0;font-size:inherit;color:var(--muted)}
.legend .sym{
  font-family:var(--serif);font-weight:700;color:var(--ink);margin-right:5px;
  white-space:nowrap;
}
.clarify{
  font-size:clamp(11px,1.2vw,14px);color:#2C4454;margin:6px 0 2px;
  padding-left:10px;border-left:3px solid var(--accent);
}
.page.dense .legend,.page.chart-heavy .legend{margin-top:2px;padding-top:2px}
.page.chart-heavy .clarify{font-size:clamp(10px,1.1vw,12px);margin:2px 0}
.page.dense .legend ul{gap:0 8px}
.page:has(.legend) .chart svg{max-height:300px}
.page.chart-heavy:has(.legend) .chart svg{max-height:200px}
.page:has(.legend) .cards{margin:8px 0}
.page:has(.legend) .flow{margin:8px 0}
"""
