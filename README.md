# Coony-Django-Transforme-se

Projeto Django preparado para rodar localmente e em produção utilizando a plataforma **Vercel**. Esta documentação descreve os pré-requisitos, variáveis de ambiente e o fluxo recomendado de deploy.

## Pré-requisitos
- Python 3.11 (definido em `runtime.txt`)
- Pip/venv para gerenciar dependências (`requirements.txt`)
- Conta na Vercel e Vercel CLI (`npm i -g vercel`)
- Banco de dados gerenciado acessível via `DATABASE_URL` (Neon, Supabase, Railway ou outro Postgres/MySQL)

## Configuração local
1. Crie o ambiente virtual: `python -m venv .venv && .venv\Scripts\activate` (PowerShell).
2. Instale dependências: `python -m pip install -r requirements.txt`.
3. Copie `.env.example` para `.env` e ajuste as chaves (secret, hosts e `DATABASE_URL`).
4. Execute as migrações: `python manage.py migrate`.
5. Popule/colecione estáticos quando necessário: `python manage.py collectstatic --noinput`.
6. Rode o servidor: `python manage.py runserver 0.0.0.0:8000`.

## Estrutura para Vercel
- `vercel.json`: define builder `@vercel/python`, aponta para `coony/wsgi.py`, adiciona comando de build para `collectstatic` e expõe `DJANGO_SETTINGS_MODULE`.
- `requirements.txt`: inclui `Django`, `django-user-agents`, `dj-database-url`, `whitenoise`, `psycopg[binary]` (driver Postgres) e `gunicorn`.
- `runtime.txt`: fixa a versão do Python suportada pelo ambiente Vercel.
- `coony/settings.py`: agora lê configurações via variáveis de ambiente, obriga `DATABASE_URL` em produção e utiliza WhiteNoise para servir arquivos estáticos diretamente no Lambda.
- `.env.example`: referência rápida das variáveis necessárias.

## Variáveis de ambiente
Configure todas na Vercel (Project Settings → Environment Variables) e localmente via `.env`:

| Nome | Descrição |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta do Django. Gere algo aleatório (`python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`). |
| `DJANGO_DEBUG` | `False` em produção. |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por vírgula (`coony.vercel.app,.vercel.app`). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Inclua `https://seu-projeto.vercel.app`. |
| `DATABASE_URL` | URL completa do banco (ex.: `postgresql://user:pass@host/db`). |

> **Uploads de mídia**: o filesystem da Vercel é somente leitura em produção. Configure um storage externo (S3, Cloudinary, etc.) e ajuste `MEDIA_URL/MEDIA_ROOT` antes de permitir upload dos usuários.

## Deploy
1. Faça login e vincule o projeto: `vercel login` → `vercel link`.
2. Cadastre as variáveis de ambiente listadas acima (`vercel env add ...`).
3. (Opcional) Sincronize as variáveis para rodar comandos locais contra o mesmo ambiente: `vercel env pull .env.production`.
4. Execute migrações contra o banco remoto a partir do seu ambiente local: `set -a && source .env.production && python manage.py migrate` (PowerShell: `Get-Content .env.production | foreach { if($_ -match '=') { $name,$value = $_.Split('='); setx $name $value } }`).
5. Realize o deploy: `vercel deploy` (pré-visualização) ou `vercel deploy --prod`.

Durante o build, a Vercel executa `python manage.py collectstatic --noinput` definido em `vercel.json`. WhiteNoise serve os arquivos empacotados diretamente do Lambda, dispensando CDN específica. Sempre que atualizar assets, lembre-se de rodar `collectstatic` localmente antes de testar.

## Próximos passos
- Integrar um armazenamento de arquivos permanente para `MEDIA_ROOT`.
- Automatizar migrações pós-deploy (GitHub Action ou comando manual após cada `vercel deploy`).
- Adicionar testes (`usuarios/tests.py`) ao pipeline antes de publicar.