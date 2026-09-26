# Canal de culinária brasileira com vídeos gerados por IA

Receitas brasileiras narradas em português, com legendas em chinês, publicadas no Bilibili.

## Pipeline

| Etapa | Ferramenta |
|---|---|
| Roteiro, narração e legendas em chinês | Claude |
| Imagens-chave e vídeo (image-to-video) | Kling 3.0 (Veo 3.1 para tomadas especiais) |
| Narração em português | ElevenLabs |
| Montagem | CapCut / DaVinci Resolve / ffmpeg |
| Publicação | Bilibili (manual por enquanto; depois automatizar com biliup) |

## Estrutura

```
canal-culinaria/
├── ferramentas/
│   └── gerar_legendas.py     # falas.tsv → narracao.txt + legendas .srt
├── personagens/
│   └── seu-valdir.md         # ficha e prompts-base do personagem
└── videos/
    └── 001-picanha-gaucha/
        ├── roteiro.md        # cenas, tomadas e prompts de imagem/vídeo
        ├── falas.tsv         # falas em português + chinês (fonte das legendas)
        ├── narracao.txt      # texto para colar no ElevenLabs
        ├── legendas.zh.srt   # legendas em chinês
        ├── legendas.pt.srt   # legendas em português
        └── bilibili.md       # título, descrição, tags e capa
```

Para editar uma fala, altere o `falas.tsv` e rode:

```
python3 ferramentas/gerar_legendas.py videos/001-picanha-gaucha
```

Arquivos grandes (MP3, MP4, imagens geradas) não devem ser commitados aqui.

## Vídeos

| # | Tema | Status |
|---|---|---|
| 001 | Picanha gaúcha no espeto | Roteiro pronto |
| 002 | Costela fogo de chão | Anunciado no 001 |
