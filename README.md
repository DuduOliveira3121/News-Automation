# News Automation

Sistema para leitura de notícias a partir de arquivos `.docx`, revisão assistida por IA e publicação automatizada em portais de notícias via Playwright.

## Arquitetura

```
src/
├── domain/          # Entidades e interfaces (sem dependências externas)
├── application/     # Use cases, serviços e DTOs
├── infrastructure/  # Banco de dados, automação web, cliente OpenAI
└── presentation/    # Interface Streamlit
```

## Requisitos

- Python 3.13+
- [Poetry](https://python-poetry.org/) (recomendado) ou `pip`

## Setup

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Instalar browsers do Playwright
playwright install chromium

# 3. Configurar variáveis de ambiente
cp .env.example .env
# edite o .env com suas credenciais

# 4. Executar
streamlit run app.py
```

## Testes

```bash
pytest
```
