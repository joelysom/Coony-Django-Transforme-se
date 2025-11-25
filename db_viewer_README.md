# Coony — DB Viewer (Tkinter)

Este utilitário local abre o arquivo `db.sqlite3` do projeto e permite que você
explore tabelas, visualize linhas, pesquise e exporte CSVs.

Características:
- Login rápido: `ADMIN` / `ADMIN`
- Tela de carregamento com progressbar
- Lista de tabelas e preview de até 1000 linhas
- Pesquisa simples (concatenando colunas)
- Exportar tabela para CSV
- Tenta carregar `logo.png` da pasta do projeto para cabecalho

Como usar:

1. Abra um terminal no diretório do projeto (onde está `manage.py`):

```powershell
cd C:\Users\JOELYSONALCANTARADAS\Desktop\django\coony
python db_viewer.py
```

2. Faça login com `ADMIN` / `ADMIN`.
3. Se desejar, clique em `Escolher DB...` para apontar para outro arquivo SQLite.
4. Selecione uma tabela na lista para ver as linhas; use `Pesquisar` para filtrar.
5. Clique em `Exportar tabela` para salvar como CSV.

Observações:
- A aplicação roda localmente e não envia dados para lugar nenhum.
- Para exibir a logo anexada, salve a imagem como `logo.png` na pasta do projeto.
- Requer `tkinter` (vem com Python em muitos sistemas) e opcionalmente `Pillow` para carregar imagens.

Se quiser que eu configure o ícone/packager (ex: pyinstaller) ou adicione mais filtros/edição de registros, me avise.
