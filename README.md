# Coony-Django-Transforme-se

Django social app pronto para rodar localmente e ser publicado na plataforma **Render.com**. Este guia explica os pré-requisitos, variáveis de ambiente e o fluxo de build/deploy automatizado via `render.yaml`.

## Pré-requisitos
- Python 3.11 (definido em `runtime.txt`).
- Gerenciador de virtualenv (venv, pipenv, etc.) e `pip` atualizado.
- Conta na Render com acesso a Web Services + Postgres (opcional, porém recomendado).
- GitHub conectado à Render (o deploy automático usa o repositório público).

## Configuração local
1. Crie o ambiente virtual: `python -m venv .venv && .\.venv\Scripts\activate` (PowerShell).
2. Instale dependências: `python -m pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e configure as variáveis (secret, hosts, `DATABASE_URL`).
4. Execute `python manage.py migrate` e, se necessário, `python manage.py createsuperuser`.
5. Gere arquivos estáticos quando testar o modo produção: `python manage.py collectstatic --noinput`.
6. Suba o servidor local: `python manage.py runserver 0.0.0.0:8000`.

## Arquivos importantes
- `render.yaml`: descreve o Web Service da Render (build, start command, env vars).
- `Procfile`: usado pela Render para iniciar o Gunicorn (`web: gunicorn coony.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --log-file -`).
- `requirements.txt` e `runtime.txt`: garantem reprodutibilidade do ambiente Python 3.11.
- `coony/settings.py`: configurações protegidas por variáveis de ambiente, WhiteNoise para servir estáticos e obrigatoriedade de `DATABASE_URL` em produção.
- `.env.example`: referência para todas as chaves necessárias localmente e no painel da Render.

## Variáveis de ambiente
Defina-as tanto no `.env` local quanto no painel da Render (Service → Environment → Environment Variables):

| Nome | Descrição |
| --- | --- |
| `DJANGO_SECRET_KEY` | Gere via `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`. |
| `DJANGO_DEBUG` | `False` em produção. |
| `DJANGO_ALLOWED_HOSTS` | Domínios separados por vírgula (`coony-django.onrender.com,.onrender.com`). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Inclua `https://coony-django.onrender.com`. |
| `DATABASE_URL` | Use Postgres da Render (URI completa) ou `sqlite:///db.sqlite3` para desenvolvimento local. |

> **Arquivos enviados pelos usuários**: Render oferece discos persistentes, mas considere provedores como S3/Cloudinary para alta disponibilidade. Ajuste `MEDIA_URL/MEDIA_ROOT` antes de liberar uploads em produção.

## Deploy na Render
1. Faça fork/clonagem do repositório no GitHub e confirme que o branch alvo (`vercel` ou outro) contém suas alterações.
2. Em `render.yaml`, ajuste `name`, `plan`, `region` e `branch` se necessário.
3. Na Render, clique em **New +** → **Blueprint** e aponte para o repositório. A plataforma lerá `render.yaml` e criará o Web Service automaticamente.
4. Preencha as variáveis marcadas com `sync: false` pelo dashboard (SECRET_KEY, DATABASE_URL, etc.).
5. O build executa `pip install`, `collectstatic` e `migrate`. Ao final o serviço inicia com `gunicorn coony.asgi:application -k uvicorn.workers.UvicornWorker` (ASGI) servindo estáticos via WhiteNoise.
6. Para implantações futuras, basta fazer push na branch monitorada. A Render reconstruirá o serviço automaticamente.

## Pós-deploy
- Conferir logs em **Render → Service → Logs** (útil após migrações ou ajustes de ambiente).
- Executar migrações manuais quando necessário via **Shell** do serviço (`python manage.py migrate`).
- Monitorar consumo de disco se estiver usando SQLite (não recomendado para produção). Considere migrar para Postgres e instalar `psycopg[binary]` caso necessário.

## Próximos passos
- Conectar um banco Postgres gerenciado e atualizar `requirements.txt` adicionando `psycopg[binary]` com a versão suportada (≥ 3.2.2).
- Configurar CDN/armazenamento para mídia do usuário.
- Adicionar testes automatizados (`usuarios/tests.py`) e integrá-los a um pipeline CI antes de cada deploy.