# Guia de reprodução e entrega

**Estado verificado:** 2026-11-23  
**Repositório:** `rochelAsc/GWO-environment`

Este guia separa os caminhos executáveis e explicita quais artefatos estão disponíveis. PFS clássico e DPFSP-DD são problemas distintos; seus motores, dados e resultados não podem ser intercambiados.

## 1. Requisitos

- Python 3.12 (CI) ou Python 3.14 (validação local registrada).
- Git.
- Para testes e scripts locais: `requirements-dev.txt`.
- Para o notebook histórico no Google Colab: dependências de `requirements-notebook.txt`; `google.colab` é fornecido pelo runtime Colab, não deve ser instalado via pip.

Na raiz do repositório:

```bash
python -m pip install -r requirements-dev.txt
```

O CI usa Python 3.12. A suíte completa também foi executada pelo responsável em Python 3.14, com 63 testes aprovados. O único warning reportado é uma depreciação emitida pelo plugin AnyIO instalado no ambiente Python 3.14.

## 2. Testes automatizados

```bash
python -m pytest -q
```

Para executar os grupos separadamente:

```bash
python -m pytest -q tests/test_dpfsp_dd.py
python -m pytest -q tests/test_discrete_gwo_dpfsp.py
python -m pytest -q tests/test_legacy_pfs.py
python -m pytest -q tests/test_legacy_gwo_characterization.py
```

Os testes de GWO legado extraem a classe histórica do export do notebook para caracterizar seu comportamento; isso não transforma o export em módulo Python importável.

## 3. DPFSP-DD: validar dados e executar o piloto

O conjunto disponível é `data/instances/DPFSP_DD.zip`. Primeiro valide todas as instâncias:

```bash
python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
```

O relatório padrão é gravado em `results/parser_validation/summary.json`. Para executar o piloto:

```bash
python -m scripts.run_gwo_pilot data/instances/DPFSP_DD.zip
```

Parâmetros padrão do piloto:
- três instâncias selecionadas deterministicamente (Small, intermediária e Large);
- quatro configurações: 30/55 lobos × decaimento linear/quadrático;
- sementes 0, 1 e 2;
- 990 avaliações reais por execução, em lotes completos de população.

Saídas:
- `results/gwo_pilot/pilot_runs.csv`;
- `results/gwo_pilot/pilot_summary.json`.

Esses resultados são um piloto técnico reduzido. Não representam a bateria confirmatória de seis configurações × 23 instâncias × 30 sementes descrita como planejamento no protocolo.

## 4. Notebook histórico PFS no Google Colab

Arquivo de entrada: `notebooks/Sistemas_Inteligentes_Entregavel.ipynb`.

1. Abra o notebook no Google Colab.
2. Clone o repositório no ambiente e trabalhe a partir da raiz do clone, para que o caminho `scripts/legacy_pfs.py` exista em `Path.cwd()/scripts/`.
3. Execute as células na ordem.
4. Quando a primeira etapa solicitar um ZIP, forneça instâncias compatíveis com o parser PFS legado.

O notebook usa `google.colab.files`, upload/download interativo e comandos mágicos `!pip`. Por isso, não é um fluxo de execução local convencional. O arquivo `scripts/sistemas_inteligentes_entregavel.py` é um export textual do notebook e também contém magics/imports exclusivos do Colab; não execute com `python scripts/sistemas_inteligentes_entregavel.py`.

**Limitação de dados:** as instâncias PFS exatas usadas nos experimentos históricos não foram recuperadas. O arquivo `DPFSP_DD.zip` não é substituto: contém instâncias DPFSP-DD, com atribuição de fábricas e due dates, enquanto o motor legado modela PFS de uma única sequência compartilhada entre máquinas. Assim, o parser e o motor são testados com fixtures sintéticas; isso não equivale a uma execução ponta a ponta do notebook. A reprodução dos resultados PFS históricos depende da recuperação das instâncias originais ou de um conjunto PFS compatível, com proveniência registrada.

## 5. O que está e o que não está reproduzível

| Item | Estado | Evidência / limite |
|---|---|---|
| Parser e avaliador DPFSP-DD | Disponível e testado | `scripts/dpfsp_dd.py`, testes e ZIP auditado |
| GWO random-key DPFSP-DD | Disponível e testado | `scripts/discrete_gwo_dpfsp.py` |
| Piloto DPFSP-DD | Executável | Quatro configurações, três instâncias e três seeds |
| Parser/avaliador PFS legado | Disponível e testado com fixtures | Formato inferido; instâncias históricas ausentes |
| Dinâmica GWO PFS legado | Caracterizada por testes | Preserva atualização sequencial/in-place |
| Notebook histórico | Executável no Colab com dados PFS compatíveis | Requer ambiente Colab e instâncias PFS |
| Bateria integral de seis configurações | Não demonstrada pelos artefatos atuais | Fuzzy/Surrogate DPFSP-DD e runner integral não estão implementados |
| Resultados históricos PFS | Não reproduzíveis integralmente neste estado | Instâncias exatas não recuperadas |

## 6. Interpretação do protocolo

`docs/experimental_protocol.md` documenta um planejamento experimental. Não confundir seus números-alvo com execuções concluídas. O piloto versionado não substitui a bateria principal. Fuzzy e Surrogate ainda exigem implementações específicas para DPFSP-DD, instrumentação, validação e testes antes de uma comparação justa.

A orientação do professor de retirar Meta-Learning está registrada em `docs/decisions/2026-11-22-scope-update.md`; não foi criada etapa substituta.

## 7. Arquivos essenciais para a entrega

- Código: `scripts/`.
- Notebook: `notebooks/Sistemas_Inteligentes_Entregavel.ipynb`.
- Instâncias DPFSP-DD: `data/instances/DPFSP_DD.zip`.
- Testes: `tests/`.
- Resultados do piloto e auditorias: `results/` e `docs/audits/`.
- Instruções: `README.md` e este guia.

Para uma submissão estritamente focada na reprodução dos experimentos PFS históricos, ainda é necessário anexar o conjunto PFS efetivamente utilizado. Não renomeie nem apresente o ZIP DPFSP-DD como se fosse esse conjunto.
