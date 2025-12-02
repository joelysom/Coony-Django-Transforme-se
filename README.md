# Coony-Django-Transforme-se

Aplicação Django preparada para desenvolvimento local e publicação na **Vercel** usando banco **Neon Postgres**. Este guia descreve o setup, variáveis de ambiente e o fluxo de deploy com funções serverless Python.

## Pré-requisitos
- Python 3.11 (definido em `runtime.txt`).
- Virtualenv ativo (`python -m venv .venv && .venv\\Scripts\\activate`).
- Conta na Vercel e Vercel CLI (`npm i -g vercel`).
- Projeto Postgres criado no Neon (ou outro provedor compatível) + string `DATABASE_URL` com `sslmode=require`.

## Configuração local
1. Instale dependências: `python -m pip install -r requirements.txt`.
2. Copie `.env.example` para `.env` e preencha as variáveis (principalmente `DJANGO_SECRET_KEY`, `DATABASE_URL`).
3. Aplique migrações: `python manage.py migrate`.
4. (Opcional) Crie um admin: `python manage.py createsuperuser`.
5. Colete estáticos para simular produção: `python manage.py collectstatic --noinput`.
6. Rode localmente: `python manage.py runserver 0.0.0.0:8000`.

## Arquivos importantes
- `vercel.json`: instrui a Vercel a usar `@vercel/python`, rodar `collectstatic` no build e direcionar todas as rotas para `coony/asgi.py`.
- `requirements.txt`: inclui Django, WhiteNoise, `uvicorn` (ASGI worker) e `psycopg[binary]` (driver Postgres para o Neon).
- `coony/settings.py`: controla DEBUG/hosts via env vars, usa `dj_database_url` e falha se `DATABASE_URL` estiver ausente em produção.
- `.env.example`: referência rápida das variáveis obrigatórias.

## Variáveis de ambiente
Configure no `.env` local e no painel da Vercel (Project → Settings → Environment Variables):

| Nome | Descrição |
| --- | --- |
| `DJANGO_SECRET_KEY` | Gere com `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`. |
| `DJANGO_DEBUG` | `False` em produção. |
| `DJANGO_ALLOWED_HOSTS` | Ex.: `coony.vercel.app,.vercel.app,localhost`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Inclua `https://coony.vercel.app` e subdomínios. |
| `DATABASE_URL` | String completa do Neon: `postgresql://<user>:<pass>@<host>/<db>?sslmode=require&channel_binding=require`. |

> **Uploads**: o filesystem do runtime Python na Vercel é somente leitura. Para `MEDIA_ROOT`, utilize storage externo (S3, Cloudinary etc.).

## Deploy na Vercel + Neon
1. Faça login (`vercel login`) e vincule o repositório (`vercel link`).
2. Cadastre as variáveis acima em Project Settings → Environment Variables.
3. Opcional: sincronize para o ambiente local com `vercel env pull .env.production`.
4. Rode migrações contra o Neon carregando o mesmo `.env.production` localmente (PowerShell: `$env:DATABASE_URL=...; python manage.py migrate`).
5. Execute `vercel deploy` para criar um preview. Quando estiver tudo ok, rode `vercel deploy --prod`.

Durante o deploy, a Vercel instala os requisitos, executa `collectstatic` e cria uma função serverless baseada em `coony/asgi.py`. O pacote `uvicorn` fornece o worker ASGI usado pelo runtime. Logs do build e runtime podem ser vistos com `vercel logs <deployment-url>`.

## Pós-deploy
- Sempre que o modelo mudar, execute migrações apontando para o Neon antes de promover para produção.
- Use `python manage.py dumpdata`/`loaddata` para transferir dados entre ambientes se necessário.
- Considere habilitar monitoramento (Sentry, etc.) e cache distribuído (Redis) para otimizar a experiência quando a base de usuários crescer.

## Próximos passos
- Automatizar migrações pós-deploy via GitHub Actions ou manualmente após cada `vercel deploy --prod`.
- Integrar storage externo para mídia.
- Expandir cobertura de testes em `usuarios/tests.py` e executá-los antes dos deploys.