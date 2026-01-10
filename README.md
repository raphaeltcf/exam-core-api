### Projeto Medway

Aqui nesse repositório temos um projeto Django básico, já configurado para uso.

Para rodar o projeto, deve-se ter o docker e ligado instalado no computador.

Para configurár o projeto, pode-se rodar o comando:

`docker compose up --build`.

Isso deve inicializá-lo na porta 8000.

Ele já vai vir com alguns modelos, alguns inclusives já populados com dados de teste, 
para facilitar o desenvolvimento.

Com o projeto rodando, para acessar o container do docker, pode-se abrir outro terminal e rodar:

`docker exec -it medway-api bash`

Uma vez dentro do container, pode-se criar um usuário/estudante com o comando:

`python manage.py createsuperuser`

E utilizar essas credenciais para acessar o admin em http://0.0.0.0:8000/admin/.
