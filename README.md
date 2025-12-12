Voxelbound — Prototype

Este diretório contém um esqueleto mínimo do jogo "Voxelbound" usando Python + Pygame.

Como executar (Windows):

1. Crie e ative um ambiente virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

3. Execute o jogo:

```powershell
python main.py
```

Controles (2D prototype):
- `WASD` ou setas: mover
- `Esc`: sair

3D Prototype (Ursina):

- Execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run3d.py
```

- Controles (3D):
- `WASD`: mover
- mouse: olhar
- `left click`: colocar bloco
- `right click`: remover bloco

Observação: o protótipo 3D usa a biblioteca `ursina`. Se ocorrerem problemas, verifique se sua versão do Python é compatível com `ursina` e instale uma versão compatível manualmente.

Observações:
- Este é apenas um protótipo minimalista para iniciar o jogo localmente.
- Se tiver problemas ao instalar `pygame`, instale uma versão compatível com sua Python (ex.: `pip install pygame==2.1.3`).
