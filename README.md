# Projeto FastAPI

Este é um projeto FastAPI configurado para rodar em um ambiente virtual Python.

## Requisitos

- **Python 3.8+**
- **pip** (gerenciador de pacotes do Python)
- **FastAPI** e **Uvicorn**

## Como Configurar o Ambiente

### 1. Criar e Ativar o Ambiente Virtual

No **Windows**, execute os seguintes comandos:

```bash
python -m venv .venv
# Para PowerShell
.\.venv\Scripts\Activate
# Para Prompt de Comando
.venv\Scripts\activate
```

### 2. Instalar as Dependências

Com o ambiente virtual ativado, instale as dependências:

```bash
pip install --no-cache-dir -r requirements.txt
```

### 3. Rodar o Servidor

Com o ambiente virtual ativado, instale as dependências:

```bash
uvicorn app.main:app --reload
```

A aplicação estará disponível em http://127.0.0.1:8000.

### Documentação
A documentação interativa da API (Swagger) estará disponível em: http://127.0.0.1:8000/docs

### Estrutura do Projeto

```bash
.
├── main.py           # Arquivo principal do FastAPI
├── requirements.txt  # Dependências do projeto
├── .venv/            # Ambiente virtual (no committ)
└── README.md         # Este arquivo
```

### Contribuição
Para contribuir, crie um fork do projeto, faça suas alterações e envie um pull request.

Esse arquivo `README.md` pode ser ajustado conforme você adiciona mais funcionalidades ao projeto.

Se precisar de mais ajuda com a configuração ou quiser ajustar o README, é só avisar!

cd .\Back-end\
.venv\Scripts\activate
uvicorn app.main:app --reload

### Gerar Tabela Local
python app/generate_table.py