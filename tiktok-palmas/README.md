# Edits de TikTok: palmas de filmes na batida da música

O script pega cenas de filmes em que alguém bate palma, encontra o instante exato de cada palma e monta vídeos verticais de 30 s. Em cada vídeo, as cenas trocam no ritmo da música e **cada palma cai exatamente em cima de uma batida**. Ele gera quantos vídeos você quiser (padrão: 100), cada um com uma combinação diferente de cenas.

Testado com clipes e música de teste: as palmas caem, em média, a 8 ms da batida (menos de meio quadro de vídeo).

## O que você precisa fornecer

1. **Cenas de filmes com palmas** → na pasta `clipes/`. Trechos de 3 a 20 s são o ideal. Veja ideias em [`cenas.md`](cenas.md). Dê ao arquivo o nome do filme (ex.: `cidadao-kane.mp4`), porque esse nome aparece na lista de créditos.
2. **A música** (arquivo mp3/m4a/wav) → na pasta `musica/`.

Quanto mais cenas diferentes, mais variados ficam os 100 vídeos. Com menos de ~20 cenas, eles vão parecer repetidos.

## Instalação (uma vez só)

1. Instale o Python: https://www.python.org/downloads/. No Windows, marque **"Add Python to PATH"** no instalador.
2. Abra o Terminal (Mac) ou o Prompt de Comando (Windows), entre nesta pasta e rode:

```
pip install -r requirements.txt
```

Isso já instala o ffmpeg junto, sem precisar instalar nada à parte.

## Uso

```
python3 palmas.py tudo
```

No Windows, use `python` no lugar de `python3`.

Pronto: sai um edit por filme (`saida/edit_<nome-do-filme>.mp4`), cada um usando só aquele filme. Edits já gerados são pulados, então dá para ir adicionando filmes aos poucos. Use `--edits-por-filme 3` para gerar variações de cada filme, ou `--misturar --quantidade 100` para misturar filmes. Cada vídeo leva uns 20 a 40 s para ser gerado, então os 100 levam cerca de 1 hora.

Por padrão, o script usa os **primeiros 30 segundos da música**.

### Em duas etapas (para revisar as palmas antes)

```
python3 palmas.py detectar
```

Abra o `palmas.csv` no Excel e apague as linhas que não forem palmas. A coluna `palmas_vizinhas` ajuda: aplausos e cenas com ritmo têm várias palmas seguidas. Depois:

```
python3 palmas.py montar --quantidade 100
```

## Ajustes úteis

| Opção | O que faz |
|---|---|
| `--inicio-musica 12.5` | começa o edit no segundo 12,5 da música (ex.: direto no refrão) |
| `--duracao 30` | duração de cada vídeo |
| `--batidas-por-corte 1` | troca de cena a cada batida (mais frenético). O padrão é 2 |
| `--layout cortar` | preenche a tela inteira cortando as laterais do filme, em vez de usar o fundo desfocado |
| `--volume-filme 0.3` | volume do som original das cenas (as palmas). 0 = mudo |
| `--sem-musica` | exporta sem a música, para você adicionar o som direto no TikTok |
| `--bpm 130` | força o BPM se a detecção automática errar |
| `--batidas batidas.txt` | usa uma lista sua de tempos das batidas (um número em segundos por linha) |
| `--sensibilidade 1..5` | na detecção: 1 = só palmas bem nítidas, 5 = pega tudo |
| `--semente 7` | gera outra leva de 100 combinações diferentes |

## Dá para varrer um filme inteiro?

Dá: coloque o filme completo em `clipes/`. A leitura é feita em blocos, então funciona até com filmes de 3 horas. Só que num filme inteiro aparecem muitos sons parecidos com palmas (portas, tiros, passos). Revise o `palmas.csv` antes de montar, ou recorte só as cenas certas. É mais rápido e dá um resultado melhor.

## Direitos autorais e TikTok

- Não existe um "número de segundos" que torne seguro usar trechos de filme; a "regra dos 7 segundos" é um mito. Cortes curtos e bem editados (aqui, cerca de 1 s por cena) são **menos** detectados automaticamente, mas não há garantia.
- A música é o que o TikTok mais detecta. O caminho mais seguro é exportar com `--sem-musica` e escolher a música na biblioteca de sons do próprio TikTok, começando do 0:00.
- Poste aos poucos e varie os vídeos: 100 vídeos quase iguais em sequência podem ser tratados como conteúdo repetitivo e perder alcance.
