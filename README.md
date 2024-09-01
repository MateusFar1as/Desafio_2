# Desafio2 - Back-end e APIs
### Organização
A solução desse desafio foi dividida em duas sub-pastas, app e db para o funcionamento do docker-compose.
Diretorio principal:
- docker-compose.yml (Arquivo docker-compose para conteinerização do app e do db)
- app (Pasta contendo a aplicação)
- db (Pasta contendo a base adventure)

app:
- database.py (Conexão com o banco de dados)
- models.py (Models do Product para o pydantic)
- routes.py (Rotas usadas na aplicação)
- logging_config.py (Configuração para o funcionamento de logging)
- auth.py (Configura o método de autenticação)
- test_main.py (Testes para as rotas)
- main.py (Arquivo principal que inicializa o projeto)
- Dockerfile (Configura o app para o docker)
- requirements.txt (Os packages usados na aplicação)

db:
- adventure.sql (Banco de dados usado na aplicação)

### Tecnologias Utilizadas
- Database: MariaDB
- Database Tool: Dbeaver
- Programming Language: Python 3
- Framework API: FastAPI
- Testes API: pytest
- Database Teste: SQLite
- Db connector: mysql.connector
- Containerization: Docker

### Utilização

##### Autenticação
username: admin
password: secret

##### Subir a API
Construir e subir o container que irá executar o uvicorn dando acesso ao API swagger em http://localhost:8000/docs#/
```bash
docker-compose up --build
```
Executar os testes unitários com o coverage:
```bash
docker-compose exec app pytest --cov
```
### Passo-a-passo
##### Tarefa 1
- Conexão banco de dados: Conexão realizada ao mariadb através do mysql.connector, usando o db que será utilizado no docker.
- Configuração API: Utilizado o FastAPI para criar os endpoints necessários, configurando rotas e métodos HTTP.
- Interação com banco de dados: Foi usado o mysql.connector para realização das queries utilizadas nas rotas.
- Validação de dados: Foi realizado o model do products com o pydantic.
- Autenticação: Autenticação via JWT com uma fake_db para as rotas de criar, atualizar e deletar. Sendo necessario o username, password e que o role do user seja admin.
- Paginação, filtração e ordenação: Foi feito checando se o user vai colocar os parametros para realizar alguma dessas ações, caso não preencha a query usara um select normal, caso ele preencha irá incrementar o que está sendo pedido.
- Criação de Logs: Os logs foram feitos utilizando o próprio logging do python, colocando os logs em app.log, com a saída sendo a data e hora, usuário que realizou a operação e os dados envolvidos.

#### Tarefa 2
- Banco de dados teste: Foi utilizado o sqlite do python através da memory, executando uma query para criar e inserir um Product para o teste.
- API teste: Feito usando o TestClient do FastAPI, configurando para cada rota criada tanto o sucesso quanto as falhas.
- Execução teste: Se utiliza do pytest e do pytest-cov.

#### Tarefa 3
- Montagem queries: Foi feita usando o dbeaver para testar o resultado e quando deu certo transferi para o python.
- Rotas: Feito usando o FastAPI, se utilizando das queries que serão executadas pelo mysql.connector.

#### Conteinerização
- Definição serviços: Feita usando docker-compose em que está definido o app e o db
- Conteinerização app: Feita usando docker-compose para definir o serviço que roda o servidor com o uvicorn, cria as portas e conecta com o ambiente do db.  Álem disso há o Dockerfile from python, copiando o app para o docker e rodando o pip install para os requirements.
- db: O serviço é feito com o docker-compose from mariadb e cria o volume átraves do banco de dados adventure salvo na pasta db, o banco de dados foi exportado átraves do mariadb cli com o mariadb-dump
