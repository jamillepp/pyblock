# PyBlock

PyBlock é uma API simples para estudo de comunicação em redes Ethereum.

## Instalação de Dependências

```bash
pip install -r requirements.txt
```

## Configuração

### Variáveis de Ambiente

Para utilizar a API, defina as variáveis de ambiente necessárias. Consulte o arquivo `.env.example` para referência. Exemplos:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/pyblock_db  # URL de conexão com o banco
AES_KEY=test_aes_key  # Chave de criptografia para as chaves privadas das contas
```

## Inicialização da API

O setup é realizado via Docker Compose. Execute o comando abaixo para iniciar todos os containers necessários:

```bash
docker compose up -d --build
```

## Testes

A API possui testes unitários utilizando `pytest`. Para executá-los, use:

```bash
pytest -v -s
```
