# Vídeo 001 — Picanha gaúcha no espeto, com o Seu Valdir

| | |
|---|---|
| Formato | Horizontal 16:9, 1080p (ou 4K), 24 fps |
| Duração | ≈ 3min15s (abertura 7s + narração ≈ 3min + encerramento 8s) |
| Idioma | Narração em português (sotaque gaúcho) + legendas em chinês |
| Personagem | [Seu Valdir](../../personagens/seu-valdir.md) |
| Narração | `narracao.txt` (≈ 2.400 caracteres, cabe folgado nos créditos grátis do ElevenLabs) |
| Legendas | `legendas.zh.srt` (chinês) e `legendas.pt.srt` (português, para conferência) |

> Os tempos abaixo são estimados. Depois de gerar o áudio, rode
> `python3 ../../ferramentas/gerar_legendas.py . --duracao <segundos do MP3>`
> para reescalar as legendas ao áudio real, e ajuste os cortes no editor.

## Ordem de produção

1. **Voz**: gerar `narracao.txt` no ElevenLabs (ver seção *Narração*). Baixar o MP3.
2. **Legendas**: reescalar as legendas com a duração real do MP3.
3. **Personagem**: gerar a imagem de referência do Seu Valdir (ficha do personagem).
4. **Imagens-chave**: gerar a imagem de cada tomada (prompts abaixo), sempre usando a referência do personagem.
5. **Vídeo**: animar cada imagem no Kling (image-to-video) com o prompt de movimento.
6. **Montagem**: no CapCut/DaVinci ou ffmpeg: clipes na ordem, narração, trilha, efeitos sonoros, `legendas.zh.srt`.
7. **Publicação**: título, descrição e tags em [`bilibili.md`](bilibili.md).

## Como ler os prompts

- `[PERSONAGEM]`, `[CENÁRIO]` e `[ESTILO]` = colar os blocos da [ficha do personagem](../../personagens/seu-valdir.md).
- **Imagem** = prompt para gerar o quadro inicial (text-to-image).
- **Movimento** = prompt para o Kling animar esse quadro (image-to-video). Use o *negative prompt* da ficha.
- O Seu Valdir **não fala na tela** (a narração é voz em off). Por isso os prompts pedem boca fechada ou sorriso, para não parecer dublagem errada.
- Gere clipes de 5s ou 10s e corte no editor para a duração indicada.

---

## Abertura (0:00 – 0:07) · sem narração

Trilha: violão de milonga começando. Som: chiado da gordura na brasa.

**A1 · 4s · close extremo**
- Imagem: `Extreme close-up of thick picanha pieces bent into C shapes on a long iron skewer over glowing charcoal embers, golden crispy fat cap, a drop of melted fat falling onto the embers, [ESTILO]`
- Movimento: `slow push-in, a drop of fat falls and makes a small flame flare up, sparks rising, smoke curling, sizzling`

**A2 · 3s · plano geral**
- Imagem: `Wide establishing shot of a rustic wooden gaucho galpão alone in the middle of green rolling pampas grassland at golden hour, thin smoke rising from the chimney, horses grazing in the distance, [ESTILO]`
- Movimento: `slow aerial drone glide towards the galpão, grass moving with the wind`
- Texto na tela (edição): **巴西高乔烤臀盖肉** / *Picanha Gaúcha*

## Cena 1 (0:07 – 0:21) · Apresentação

> Buenas, tchê! Seja bem-vindo ao meu galpão, aqui no coração dos pampas, no Rio Grande do Sul. Eu sou o Seu Valdir, e faz mais de quarenta anos que eu cuido do fogo de churrasco.

**1a · 7s**
- Imagem: `[PERSONAGEM] stepping into the galpão entrance, touching the brim of his hat in greeting, warm closed-mouth smile, medium shot, [CENÁRIO], [ESTILO]`
- Movimento: `he walks two steps towards the camera and tips his hat with a friendly nod, mouth closed, smiling, camera slowly pulls back`

**1b · 7s**
- Imagem: `[PERSONAGEM] standing beside the brick barbecue pit, one hand open in a welcoming gesture, pampas visible behind him, medium wide shot, [CENÁRIO], [ESTILO]`
- Movimento: `he opens his arm in a welcoming gesture and looks proudly around the galpão, gentle smile, slow lateral camera move`

## Cena 2 (0:21 – 0:32) · O tema do vídeo

> E hoje eu vou te ensinar a fazer a rainha do churrasco brasileiro: a picanha. Então pega teu chimarrão, te acomoda, que a prosa vai ser boa.

**2a · 5s**
- Imagem: `[PERSONAGEM] holding up a whole raw picanha with a thick white fat cap with both hands over a wooden cutting board, proud expression, [CENÁRIO], [ESTILO]`
- Movimento: `he lifts the picanha slightly towards the camera with a proud smile, camera slowly pushes in`

**2b · 6s**
- Imagem: `[PERSONAGEM] sitting on a wooden bench inside the galpão, sipping chimarrão from a gourd with a silver bombilla, relaxed, [CENÁRIO], [ESTILO]`
- Movimento: `he sips the chimarrão calmly and lowers the gourd, relaxed smile, steam from a kettle beside him, static camera`

## Cena 3 (0:32 – 0:54) · Escolhendo a picanha

> Tudo começa no açougue. A picanha boa pesa entre um quilo e um quilo e quatrocentos. Mais do que isso, bah, já veio pedaço de alcatra junto. Olha essa capa de gordura: tem que ter a grossura de um dedo, branquinha e firme. É ela que dá o sabor e deixa a carne suculenta. Nunca, jamais, tira essa gordura!

**3a · 5s**
- Imagem: `Top-down shot of a whole raw picanha (beef rump cap), triangular shape, deep red meat with an even thick white fat cap, on a thick rustic wooden cutting board, coarse salt bowl and a butcher knife beside it, [ESTILO]`
- Movimento: `slow overhead rotation of the camera around the cutting board`

**3b · 6s**
- Imagem: `Close-up of weathered hands of an old gaucho placing a whole raw picanha on a vintage brass kitchen scale on a wooden table, [CENÁRIO], [ESTILO]`
- Movimento: `the hands gently place the picanha on the scale, the scale needle moves and settles, shallow depth of field`

**3c · 6s**
- Imagem: `Macro shot of the thick white fat cap of a raw picanha, about one centimeter thick, firm and clean, showing the layer between fat and red meat, [ESTILO]`
- Movimento: `slow macro slide along the fat cap edge, light reflecting on the fat`

**3d · 5s**
- Imagem: `[PERSONAGEM] looking at the camera and wagging his index finger in a playful "no" gesture, eyebrows raised, closed-mouth smile, medium close-up, [CENÁRIO], [ESTILO]`
- Movimento: `he wags his finger side to side in a playful warning, then chuckles, static camera`

## Cena 4 (0:54 – 1:14) · O fogo

> Agora, o fogo. Aqui no Sul a gente usa lenha, ou um carvão de qualidade. Acende com calma e espera. O segredo do churrasqueiro é paciência: carne não se assa na chama, se assa na brasa. Quando o carvão estiver coberto por uma cinza branquinha, aí sim, tá pronto.

**4a · 6s**
- Imagem: `[PERSONAGEM] kneeling at a long brick barbecue pit, arranging split eucalyptus firewood and lump charcoal, [CENÁRIO], [ESTILO]`
- Movimento: `he places a log on the pile and lights it, flames start to rise, camera slowly moves in`

**4b · 7s**
- Imagem: `Close-up of tall orange flames burning firewood and charcoal in a brick barbecue pit, [ESTILO]`
- Movimento: `time-lapse, the flames slowly die down and the wood turns into glowing red embers`

**4c · 6s**
- Imagem: `Macro shot of charcoal embers covered in a thin layer of white ash with bright orange glow underneath, [ESTILO]`
- Movimento: `embers pulsing with light, a soft breeze makes the glow intensify, tiny sparks rising`

## Cena 5 (1:14 – 1:24) · O truque da mão

> Um truque antigo: coloca a mão na altura onde vai ficar a carne. Se tu aguentar uns cinco, seis segundos, o fogo tá no ponto certo.

**5a · 10s**
- Imagem: `[PERSONAGEM] holding his open palm flat above the glowing embers at skewer height, concentrated expression, side view, [CENÁRIO], [ESTILO]`
- Movimento: `he holds his palm steady over the heat for a few seconds, then pulls his hand back, shakes it lightly and nods with a satisfied smile, mouth closed`

## Cena 6 (1:24 – 1:39) · O corte em bifes

> Voltemos à picanha. Eu corto ela em bifes bem grossos, da largura de três dedos, sempre a favor da fibra. Assim, na hora de servir, a gente fatia contra a fibra e a carne fica macia que é uma barbaridade.

**6a · 8s**
- Imagem: `Overhead shot of weathered hands cutting a raw picanha into thick steaks with a large butcher knife on a wooden cutting board, cutting along the grain, [ESTILO]`
- Movimento: `the knife slices slowly and cleanly through the meat, one thick steak falls to the side, steady overhead camera`

**6b · 7s**
- Imagem: `Three thick raw picanha steaks, about 5 cm wide each, lined up on a wooden cutting board, fat cap on top of each, [ESTILO]`
- Movimento: `slow dolly along the three steaks, soft golden light`

## Cena 7 (1:39 – 1:49) · Dobrar e espetar

> Agora dobra o bife em forma de meia-lua, com a gordura para fora, e passa o espeto bem no meio. Olha que beleza, parece uma ferradura!

**7a · 6s**
- Imagem: `Close-up of hands folding a thick raw picanha steak into a C shape with the fat cap on the outside and pushing a long iron skewer through the middle, [ESTILO]`
- Movimento: `the hands bend the steak into a half-moon and slide the skewer through it`

**7b · 4s**
- Imagem: `[PERSONAGEM] holding up a long iron skewer with three C-shaped raw picanha pieces, fat cap facing outwards like horseshoes, admiring it, [CENÁRIO], [ESTILO]`
- Movimento: `he raises the skewer and turns it slowly to show it, proud smile`

## Cena 8 (1:49 – 1:58) · Sal grosso

> E o tempero? Sal grosso. Só isso, tchê. Carne boa não precisa de mais nada. Espalha bem por todos os lados, sem medo.

**8a · 5s**
- Imagem: `A hand sprinkling coarse rock salt over C-shaped raw picanha pieces on an iron skewer, salt crystals in the air, [ESTILO]`
- Movimento: `slow motion, salt crystals fall and bounce on the meat and fat`

**8b · 4s**
- Imagem: `Macro shot of coarse salt crystals resting on the white fat cap of raw picanha, [ESTILO]`
- Movimento: `slow focus pull across the salt crystals`

## Cena 9 (1:58 – 2:12) · Assar alto e devagar

> Leva pra churrasqueira, primeiro bem alto, longe da brasa. Deixa uns vinte e cinco minutos, para a gordura ir derretendo devagarinho e escorrendo pela carne. Esse é o momento de ter calma.

**9a · 6s**
- Imagem: `[PERSONAGEM] placing a skewer of salted picanha on the highest level of a brick barbecue pit, far above the glowing embers, [CENÁRIO], [ESTILO]`
- Movimento: `he rests the skewer on the top rack support and steps back, light smoke rising`

**9b · 8s**
- Imagem: `Close-up of picanha on a skewer slowly roasting high above embers, the fat cap starting to turn translucent and glisten, [ESTILO]`
- Movimento: `time-lapse, the fat slowly melts and drips down the meat, the surface turns golden, smoke drifting`

## Cena 10 (2:12 – 2:22) · O mate e a roda

> Enquanto isso, um mate. Churrasco, pra gaúcho, não é só comida: é reunir a família, os amigos, e jogar conversa fora em volta do fogo.

**10a · 6s**
- Imagem: `[PERSONAGEM] sitting by the barbecue pit sipping chimarrão and watching the fire, peaceful expression, [CENÁRIO], [ESTILO]`
- Movimento: `he sips the chimarrão slowly, firelight flickering on his face, static camera`

**10b · 4s**
- Imagem: `Wide shot of a Brazilian family and friends of different ages laughing and talking around a barbecue pit inside a rustic galpão at dusk, warm firelight, [ESTILO]`
- Movimento: `people laughing and passing a chimarrão gourd, slow camera drift, warm atmosphere`

## Cena 11 (2:22 – 2:37) · Dourar e bater o sal

> Passado o tempo, baixa o espeto pra perto da brasa, uns cinco minutinhos de cada lado, pra dourar e fazer aquela casquinha. Antes de tirar, bate o espeto com as costas da faca, pra cair o excesso de sal.

**11a · 5s**
- Imagem: `[PERSONAGEM] moving a skewer of roasting picanha down to the lowest level close to the embers, [CENÁRIO], [ESTILO]`
- Movimento: `he lowers the skewer near the embers, a flare of heat and a burst of sizzle`

**11b · 6s**
- Imagem: `Close-up of picanha on a skewer with a deep golden-brown crispy crust and bubbling fat, very close to glowing embers, [ESTILO]`
- Movimento: `fat bubbling and sizzling on the crust, a small flame licks up, slow push-in`

**11c · 4s**
- Imagem: `Close-up of a hand tapping the iron skewer of roasted picanha with the back of a knife, excess salt falling off, [ESTILO]`
- Movimento: `two firm taps with the back of the knife, salt crystals fall off in slow motion`

## Cena 12 (2:37 – 2:51) · Fatiar

> Agora a hora mais esperada. Na tábua, fatia bem fininho, contra a fibra. Olha só essa cor: douradinha por fora, rosada por dentro, e o suco escorrendo. Isso aqui é ponto de gaúcho!

**12a · 7s**
- Imagem: `Close-up of roasted picanha on a wooden cutting board being sliced thinly against the grain with a sharp knife, golden crust, pink center, juices on the board, [ESTILO]`
- Movimento: `the knife slices through the meat, a thin slice falls revealing the juicy pink center, juices running`

**12b · 7s**
- Imagem: `Macro shot of thin slices of medium-rare picanha fanned out on a wooden board, golden crispy fat edge, pink juicy center glistening, [ESTILO]`
- Movimento: `slow push-in, juices glistening, a little steam rising`

## Cena 13 (2:51 – 2:57) · À mesa

> Serve com pão, farofa e uma salada fresca, e chama a gurizada pra mesa.

**13a · 6s**
- Imagem: `Rustic wooden table inside a gaucho galpão with a board of sliced picanha, crusty bread, a clay bowl of farofa, a tomato and onion salad, glasses of red wine, children's hands reaching for the meat, [ESTILO]`
- Movimento: `hands reach in and take slices, laughter, slow overhead camera move`

## Cena 14 (2:57 – 3:09) · Despedida

> Gostou, tchê? Então deixa teu joinha, tua moedinha e salva o vídeo, que no próximo eu te ensino a fazer uma costela fogo de chão. Um quebra-costela e até a próxima!

**14a · 7s**
- Imagem: `[PERSONAGEM] looking at the camera and raising his chimarrão gourd in a toast, winking, closed-mouth smile, medium close-up, [CENÁRIO], [ESTILO]`
- Movimento: `he raises the gourd towards the camera and winks, warm smile, static camera`

**14b · 5s**
- Imagem: `[PERSONAGEM] seen from behind walking out of the galpão towards the pampas at sunset, waving one hand over his shoulder, [ESTILO]`
- Movimento: `he walks away slowly while waving goodbye, golden sunset, camera stays still`

## Encerramento (3:09 – 3:17) · sem narração

**E1 · 8s**
- Imagem: `Wide shot of the galpão at dusk with the fire glowing inside and silhouettes of a family around a table, pampas under an orange and purple sky, [ESTILO]`
- Movimento: `very slow pull-back, first stars appearing, smoke rising`
- Texto na tela (edição): **下期预告：地火烤牛肋排** / *Próximo: costela fogo de chão* e o lembrete **一键三连！**

---

## Narração (ElevenLabs)

- Texto: copiar `narracao.txt` inteiro (≈ 2.400 caracteres).
- Modelo: **Eleven Multilingual v2** (mais estável) ou **Eleven v3** (mais expressivo).
- Voz: masculina, madura, calorosa, português brasileiro (ver ficha do personagem).
- Ajustes sugeridos: Stability ≈ 45%, Similarity ≈ 75%, Style ≈ 20%, Speed ≈ 0,95.
- Os créditos grátis (≈ 10.000 caracteres/mês) dão para gerar a narração inteira umas 3 a 4 vezes. Se só um trecho ficar ruim, gere de novo só aquele parágrafo em vez do texto todo.
- O sotaque gaúcho de verdade é difícil de conseguir numa voz genérica. Teste 2 ou 3 vozes antes de gastar créditos com o texto inteiro.

## Som e trilha

- Trilha: instrumental de milonga ou chamamé com violão, livre de direitos. Volume baixo (cerca de −20 dB) debaixo da narração.
- Efeitos: chiado da gordura na brasa, fogo crepitando, vento no campo, cuia de chimarrão. Use uma biblioteca livre ou os efeitos sonoros do ElevenLabs, se sobrarem créditos.

## Custo estimado de vídeo (Kling)

≈ 200 s de clipes. A cerca de US$ 0,10–0,14 por segundo, dá **US$ 20–28**, mais as tomadas refeitas. Conte com **US$ 35–50** no total.
