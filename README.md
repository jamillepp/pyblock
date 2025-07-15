# PyBlock

PyBlock é uma API simples para estudo de comunicação em redes Ethereum.

## Instalação de Dependências

```bash
pip install -r requirements.txt
```

## Configuração

### Variáveis de Ambiente

Defina as variáveis de ambiente necessárias para utilizar a API. Consulte o arquivo `.env.example` para referência. Exemplo:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/pyblock_db  # URL de conexão com o banco
AES_KEY=test_aes_key  # Chave de criptografia para as chaves privadas das contas
PROVIDER_URLhttps://sepolia.infura.io/v3/{API_KEY} # Url para conexão do Web3 com a rede
```

## Inicialização da API

O setup é realizado via Docker Compose. Execute o comando abaixo para iniciar todos os containers necessários:

```bash
docker compose up -d --build
```

## Testes

### Configuração para Testes

Para testar a API, defina as variáveis de ambiente necessárias. Use dados personalizados e reais para que os testes funcionem corretamente. Exemplo:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/pyblock_db
AES_KEY=7071...5b98
PROVIDER_URLhttps://sepolia.infura.io/v3/{API_KEY}

ETH_TX_HASH=0xa5...86
ERC20_TX_HASH=0xb1...3a

ACC2_ADDRESS=0xBD...c7e
ACC1_ADDRESS=0x3a...97

CONTRACT_ASSET=GLD
CONTRACT_ADDRESS=0x06...a8
```

### Rodando os Testes

A API possui testes unitários utilizando `pytest`. Para executá-los, use:

```bash
pytest -v -s
```

# Documentação

Esta API é feita com FastAPI, por isso uma documentação no swagger é gerada em `http://localhost:8000/docs` quando ela está de pé.