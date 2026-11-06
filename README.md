# Portal CEU Aricanduva

Protótipo acadêmico do Projeto Integrador (UNIVESP, Engenharia da Computação).
Portal web acessível para avisos escolares, agenda cultural e cadastro de munícipes.

## Tecnologias
- **Framework web:** Flask (Python)
- **Banco de dados:** SQLite
- **API REST:** `/api/avisos`, `/api/eventos`, `/api/municipes`, `/api/saude`
- **Script web:** JavaScript (acessibilidade, validação e consumo da API)
- **Acessibilidade:** HTML5 semântico, WAI-ARIA, alto contraste, ajuste de fonte, navegação por teclado
- **Testes:** `unittest` (API e validação de CPF) + auditoria Lighthouse
- **Nuvem:** Render (ver `render.yaml`)
- **Controle de versão:** Git/GitHub

## Rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                    # http://localhost:5000
```
Código de acesso da secretaria (local): `troque-este-token`
(defina outro com a variável `ADMIN_TOKEN`).

## Testes
```bash
python -m unittest discover -s tests -v
```

## Estrutura
```
app.py            API Flask + SQLite
static/           front-end (index.html, style.css, script.js)
tests/            testes automatizados
render.yaml       configuração de deploy
```
