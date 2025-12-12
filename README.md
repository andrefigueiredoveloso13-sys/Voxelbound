Voxelbound — Prototype

Este diretório contém o protótipo 3D do jogo "Voxelbound" implementado com Python + Ursina.

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

3. Execute o protótipo 3D:

```powershell
python run3d.py
```

Controles (3D):
- `WASD`: mover
- mouse: olhar
- `left click`: colocar bloco
- `right click`: remover bloco
- `1`-`4`: selecionar tipo de bloco (hotbar)
- `1`-`9`: selecionar slot da hotbar
- `I`: abrir/fechar inventário
- `F5`: salvar mundo (`world.json`)
- `F9`: carregar mundo (`world.json`)
- `L`: alternar iluminação direcional

Os blocos são salvos como uma lista de posições e índices de cor em `world.json` na raiz do projeto.

Observação: o protótipo 3D usa a biblioteca `ursina`. Se ocorrerem problemas, verifique se sua versão do Python é compatível com `ursina`.
