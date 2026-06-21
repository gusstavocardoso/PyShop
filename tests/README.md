# 🧪 PyShop — Suite de Testes

Suite completa com três níveis de testes para o PyShop.

## 📁 Estrutura

```
tests/
├── conftest.py              # Fixtures compartilhadas (banco, client, dados)
├── requirements-test.txt    # Dependências de teste
├── unit/
│   └── test_unit.py         # Testes unitários (sem I/O)
├── integration/
│   └── test_integration.py  # Testes de integração (API + SQLite)
└── e2e/
    └── test_e2e.py          # Testes E2E (Playwright + browser real)
```

## ⚡ Setup

### 1. Instalar dependências de teste
```bash
cd pyshop/backend
pip install -r ../tests/requirements-test.txt
```

### 2. Instalar browsers do Playwright (apenas para E2E)
```bash
playwright install chromium
```

---

## 🔬 Testes Unitários

Testam funções e lógica isolada. **Não precisam de banco ou servidor.**

```bash
# Rodar apenas unitários
cd pyshop/backend
pytest ../tests/unit/ -v

# Com relatório de cobertura
pytest ../tests/unit/ -v --cov=. --cov-report=term-missing
```

### O que é testado:
| Classe | Cobertura |
|--------|-----------|
| `TestProductSchemas` | Validação de entrada, defaults, tipos |
| `TestOrderSchemas` | Criação de pedido, items obrigatórios |
| `TestOrderTotalCalculation` | Cálculo de total, arredondamento |
| `TestProductModel` | Atributos do modelo, nomes de tabela |
| `TestImageUrlConstruction` | Geração e correção de URLs |
| `TestPriceFormatting` | Formatação R$ no padrão BR |
| `TestStockValidation` | Validação de estoque disponível |

---

## 🔗 Testes de Integração

Testam os endpoints da API com banco **SQLite em memória**. **Não precisam do Docker.**

```bash
# Rodar apenas integração
cd pyshop/backend
pytest ../tests/integration/ -v

# Com relatório de cobertura HTML
pytest ../tests/integration/ -v --cov=. --cov-report=html:../tests/coverage_html
```

### O que é testado:
| Endpoint | Cenários |
|----------|----------|
| `GET /` | Status 200, mensagem PyShop |
| `GET /health` | `{"status": "ok"}` |
| `GET /products/` | Listagem, filtro por categoria, banco vazio |
| `GET /products/categories` | Sem duplicatas, tipos corretos |
| `GET /products/{id}` | Existente, 404, ID inválido (422) |
| `POST /orders/` | Sucesso, total correto, carrinho vazio (400), produto inexistente (404), estoque insuficiente (400), campos ausentes (422) |
| `GET /orders/{id}` | Existente, 404, ID inválido |

---

## 🌐 Testes E2E (Playwright)

Testam o fluxo completo no browser. **Requerem `docker compose up` rodando.**

```bash
# Certifique-se que os containers estão rodando:
docker compose up -d

# Rodar E2E headless (CI)
cd pyshop/backend
pytest ../tests/e2e/ -v

# Rodar E2E com browser visível
pytest ../tests/e2e/ -v --headed

# Rodar com slowmo para acompanhar o fluxo
pytest ../tests/e2e/ -v --headed --slowmo=500

# Gerar relatório HTML do Playwright
pytest ../tests/e2e/ -v --html=../tests/e2e_report.html
```

### O que é testado:
| Classe | Cenários |
|--------|----------|
| `TestHomePage` | Título, logo, hero, grid, imagens carregadas, badge |
| `TestCategoryFilter` | Pills visíveis, filtro por categoria, voltar para Todos |
| `TestAddToCart` | Toast de confirmação, badge reativo, incremento |
| `TestCartPage` | Carrinho vazio, item adicionado, subtotal, + / -, remover |
| `TestCheckoutPage` | Formulário, validação, fluxo completo, tela de sucesso |
| `TestNavigation` | Logo, ícone carrinho, link Produtos |

---

## 🚀 Rodar Tudo de Uma Vez

```bash
cd pyshop/backend

# Unitários + Integração (sem Docker)
pytest ../tests/unit/ ../tests/integration/ -v --cov=. --cov-report=term-missing

# Tudo incluindo E2E (com Docker rodando)
pytest ../tests/ -v --ignore=../tests/e2e/  # sem E2E
pytest ../tests/ -v                          # com E2E
```

## 📊 Relatório de Cobertura

Após rodar com `--cov-report=html`, abra:
```
tests/coverage_html/index.html
```

---

## 🛠️ Configuração do pytest

O arquivo `backend/pyproject.toml` já configura:
- Diretório de testes: `tests/`
- Cobertura automática no relatório
- Modo asyncio automático
- Supressão de DeprecationWarnings
