#!/usr/bin/env python3
"""Gera narracao.txt e legendas .srt (pt e zh) a partir do falas.tsv de um vídeo.

Uso:
    python3 gerar_legendas.py ../videos/001-picanha-gaucha
    python3 gerar_legendas.py ../videos/001-picanha-gaucha --duracao 178.4 --inicio 7

Sem --duracao, os tempos são estimados pelo ritmo médio de fala.
Depois de gerar o áudio no ElevenLabs, rode de novo passando a duração
real do MP3 (em segundos) para reescalar todas as legendas. --inicio é o
segundo do vídeo em que a narração começa (depois da abertura sem fala).
"""
import argparse
import csv
import pathlib

CARACTERES_POR_SEGUNDO = 14.5  # ritmo de uma narração calma em português
DURACAO_MINIMA = 1.2
PAUSA_ENTRE_FRASES = 0.15
PAUSA_ENTRE_CENAS = 0.8
INICIO = 7.0  # abertura sem fala antes da narração (padrão; ajuste com --inicio)


def ler_falas(pasta):
    with open(pasta / "falas.tsv", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def estimar_tempos(falas, inicio):
    tempos, t, cena_anterior = [], inicio, None
    for fala in falas:
        if cena_anterior is not None:
            t += PAUSA_ENTRE_CENAS if fala["cena"] != cena_anterior else PAUSA_ENTRE_FRASES
        dur = max(DURACAO_MINIMA, len(fala["pt"]) / CARACTERES_POR_SEGUNDO)
        tempos.append((t, t + dur))
        t += dur
        cena_anterior = fala["cena"]
    return tempos


def reescalar(tempos, duracao_real, inicio):
    fator = duracao_real / (tempos[-1][1] - inicio)
    return [(inicio + (a - inicio) * fator, inicio + (b - inicio) * fator) for a, b in tempos]


def srt_tempo(s):
    ms = round(s * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    seg, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{seg:02},{ms:03}"


def escrever_srt(caminho, falas, tempos, idioma):
    blocos = [
        f"{i}\n{srt_tempo(a)} --> {srt_tempo(b)}\n{fala[idioma]}\n"
        for i, (fala, (a, b)) in enumerate(zip(falas, tempos), 1)
    ]
    caminho.write_text("\n".join(blocos), encoding="utf-8")


def escrever_narracao(caminho, falas):
    paragrafos, atual, cena = [], [], None
    for fala in falas:
        if cena is not None and fala["cena"] != cena:
            paragrafos.append(" ".join(atual))
            atual = []
        atual.append(fala["pt"])
        cena = fala["cena"]
    paragrafos.append(" ".join(atual))
    texto = "\n\n".join(paragrafos) + "\n"
    caminho.write_text(texto, encoding="utf-8")
    return len(texto)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pasta", type=pathlib.Path, help="pasta do vídeo (contém falas.tsv)")
    p.add_argument("--duracao", type=float, help="duração real do áudio da narração, em segundos")
    p.add_argument("--inicio", type=float, default=INICIO, help="segundo do vídeo em que a narração começa")
    args = p.parse_args()

    falas = ler_falas(args.pasta)
    tempos = estimar_tempos(falas, args.inicio)
    if args.duracao:
        tempos = reescalar(tempos, args.duracao, args.inicio)

    escrever_srt(args.pasta / "legendas.pt.srt", falas, tempos, "pt")
    escrever_srt(args.pasta / "legendas.zh.srt", falas, tempos, "zh")
    caracteres = escrever_narracao(args.pasta / "narracao.txt", falas)

    print(f"narracao.txt: {caracteres} caracteres | narração termina em {tempos[-1][1]:.1f}s\n")
    print("cena  início   fim     duração")
    cenas = {}
    for fala, (a, b) in zip(falas, tempos):
        ini, _ = cenas.get(fala["cena"], (a, b))
        cenas[fala["cena"]] = (ini, b)
    for cena, (a, b) in cenas.items():
        print(f"{cena:>4}  {a:6.1f}  {b:6.1f}  {b - a:6.1f}s")


if __name__ == "__main__":
    main()
