# AGENTS.md: SkyLux Aircraft Care (manual comum a todos os agentes de IA)

Site estático de uma página da SkyLux Aviation (detalhamento de aeronaves, Van Nuys/VNY, Los Angeles). Publicado em `skylux-aviation.com` (ver `CNAME`). Não há build nem dependências.

## Mapa (leia só o trecho necessário; não abra arquivos inteiros sem precisar)
| O quê | Onde | Como achar sem ler tudo |
|---|---|---|
| Seções da página | `index.html` (~520 linhas) | `grep -n '^<!-- ' index.html` lista NAVBAR, HERO, MARQUEE, FEATURES, SERVICES, WHY, GALLERY, TESTIMONIALS, AREAS, CONTACT e FOOTER com o número da linha; depois, Read com offset/limit |
| Estilos | `assets/css/style.css` (~27 KB) | `grep -n '<seletor>'` |
| Comportamento e formulário | `assets/js/main.js` (~4 KB) | o envio vai para `https://api.web3forms.com/submit`; a `access_key` fica num input hidden no `index.html` (seção CONTACT) |
| Imagens | `assets/images/` (`gl-*`, `gallery-*`, `hero-jet.jpg`, `og-image.png`) | `ls` |
| Fotos originais | `IMG_*.HEIC` na raiz (~1 MB cada) | binários: nunca abrir como texto |

## Regras
- Ao alterar CSS ou JS, atualize o cache-bust `?v=<timestamp>` no `<link>`/`<script>` correspondente do `index.html`.
- Contatos oficiais: `Info@skylux-aviation.com`, +1 (213) 696-5737. Mantenha-os iguais no CONTACT e no FOOTER.
- Preview local: `python3 -m http.server 8791` (já configurado em `.claude/launch.json`).
- Não troque a `access_key` do Web3Forms sem pedido explícito (ela foi verificada para entregar ao email acima).

## Contexto global (segundo cérebro)
O contexto transversal do Alexandre (perfil, contatos, outras frentes) fica no repositório privado
`aledcanova/segundo-cerebro`. Se ele não estiver nesta sessão, anexe-o (add_repo / clone) e rode lá
`python3 tools/brain.py brief` e `python3 tools/brain.py card skylux`. Fatos novos e duráveis
sobre este projeto: `python3 tools/brain.py nota skylux "<fato> (fonte: ...)"`. As regras deste repositório têm precedência.
