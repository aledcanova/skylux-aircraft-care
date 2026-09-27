#!/usr/bin/env python3
"""Edits de TikTok: cenas de filmes com palmas sincronizadas na batida de uma música.

Passo a passo:
    1. Coloque os trechos de filme (ou filmes inteiros) em clipes/
    2. Coloque a música em musica/ (mp3, wav, m4a...)
    3. python3 palmas.py detectar        -> encontra as palmas e grava palmas.csv
       (abra o palmas.csv e apague as linhas que não forem palmas, se quiser)
    4. python3 palmas.py montar --quantidade 100
                                         -> gera saida/edit_001.mp4 ... edit_100.mp4

    Ou tudo de uma vez:  python3 palmas.py tudo --quantidade 100

Dependências:  pip install numpy imageio-ffmpeg
"""
import argparse
import csv
import pathlib
import random
import re
import shutil
import subprocess
import sys

import numpy as np

PASTA = pathlib.Path(__file__).resolve().parent
EXTENSOES_VIDEO = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
EXTENSOES_AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

SR = 16000          # taxa de amostragem da análise (palmas têm energia até ~8 kHz)
JANELA = 512        # 32 ms
PASSO = 128         # 8 ms entre quadros de análise
FPS = 30
LARGURA, ALTURA = 1080, 1920


# ---------------------------------------------------------------- ffmpeg

def ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg não encontrado. Rode: pip install imageio-ffmpeg")


def info_midia(arquivo):
    """Duração em segundos e se o arquivo tem áudio."""
    r = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(arquivo)],
                       capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    if not m:
        return 0.0, False
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s), "Audio:" in r.stderr


def ler_audio_em_blocos(arquivo, segundos_por_bloco=60):
    """Decodifica o áudio em mono/16 kHz aos poucos (funciona com filmes de 2h+)."""
    proc = subprocess.Popen(
        [ffmpeg_bin(), "-v", "error", "-i", str(arquivo), "-vn", "-ac", "1",
         "-ar", str(SR), "-f", "s16le", "-"],
        stdout=subprocess.PIPE)
    tamanho = SR * segundos_por_bloco * 2
    while True:
        dados = proc.stdout.read(tamanho)
        if not dados:
            break
        yield np.frombuffer(dados[: len(dados) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768
    proc.wait()


# ---------------------------------------------------------------- análise de áudio

def espectrograma(arquivo):
    """Magnitude do espectro quadro a quadro, calculada em blocos para economizar memória."""
    janela = np.hanning(JANELA).astype(np.float32)
    resto = np.zeros(0, dtype=np.float32)
    partes = []
    for bloco in ler_audio_em_blocos(arquivo):
        x = np.concatenate([resto, bloco])
        n = 1 + (len(x) - JANELA) // PASSO if len(x) >= JANELA else 0
        if n > 0:
            quadros = np.lib.stride_tricks.sliding_window_view(x, JANELA)[::PASSO][:n]
            partes.append(np.abs(np.fft.rfft(quadros * janela, axis=1)).astype(np.float32))
            resto = x[n * PASSO:]
        else:
            resto = x
    if not partes:
        return np.zeros((0, JANELA // 2 + 1), dtype=np.float32)
    return np.concatenate(partes)


def fluxo(espec, f_min, f_max):
    """Aumento de energia (spectral flux) numa faixa de frequência."""
    freqs = np.fft.rfftfreq(JANELA, 1 / SR)
    faixa = (freqs >= f_min) & (freqs <= f_max)
    log = np.log1p(100 * espec[:, faixa])
    d = np.diff(log, axis=0, prepend=log[:1])
    return np.maximum(d, 0).mean(axis=1)


def planura(espec, f_min=1000, f_max=7000):
    """Spectral flatness: perto de 1 = ruído (palma), perto de 0 = tom (voz, música)."""
    freqs = np.fft.rfftfreq(JANELA, 1 / SR)
    faixa = espec[:, (freqs >= f_min) & (freqs <= f_max)] + 1e-9
    return np.exp(np.log(faixa).mean(axis=1)) / faixa.mean(axis=1)


def picos(sinal, limiar_relativo, distancia_min_s):
    """Máximos locais acima de mediana + k * desvio (limiar adaptativo em janela de ~3 s)."""
    if len(sinal) == 0:
        return np.array([], dtype=int)
    viz = max(1, int(0.05 * SR / PASSO))
    janela_local = int(3 * SR / PASSO)
    base = np.array([np.median(sinal[max(0, i - janela_local): i + janela_local])
                     for i in range(0, len(sinal), viz)]).repeat(viz)[: len(sinal)]
    desvio = np.median(np.abs(sinal - np.median(sinal))) + 1e-9
    limiar = base + limiar_relativo * desvio
    candidatos = [i for i in range(len(sinal))
                  if sinal[i] > limiar[i]
                  and sinal[i] == sinal[max(0, i - viz): i + viz + 1].max()]
    escolhidos, ultimo = [], -1e9
    dist = distancia_min_s * SR / PASSO
    for i in sorted(candidatos, key=lambda i: -sinal[i]):
        if all(abs(i - j) >= dist for j in escolhidos):
            escolhidos.append(i)
    return np.array(sorted(escolhidos), dtype=int)


def detectar_palmas_arquivo(arquivo, sensibilidade):
    espec = espectrograma(arquivo)
    if len(espec) < 20:
        return []
    f = fluxo(espec, 1500, 7000)
    plan = planura(espec)
    freqs = np.fft.rfftfreq(JANELA, 1 / SR)
    energia = (espec[:, (freqs >= 1500) & (freqs <= 7000)] ** 2).sum(axis=1)
    # Palma = ataque forte, ruidoso nos ~30 ms seguintes (voz e instrumentos viram tom)
    # e que some rápido: 80 ms depois a energia já caiu bem.
    n = len(f)
    depois = np.array([plan[i: i + 4].mean() for i in range(n)])
    idx_decaimento = np.minimum(np.arange(n) + int(0.08 * SR / PASSO), n - 1)
    decai = energia[idx_decaimento] < 0.35 * energia
    sinal = f * np.clip(depois * 3, 0, 1) * decai
    limiar = {1: 14, 2: 10, 3: 7, 4: 5, 5: 3.5}[sensibilidade]
    idx = picos(sinal, limiar, 0.12)
    # quanto a palma se destaca do som ao redor (±1 s): cliques e ruídos baixos ficam de fora
    w = int(SR / PASSO)
    snr = np.array([10 * np.log10(energia[i: i + 3].max() / (np.median(energia[max(0, i - w): i + w]) + 1e-12))
                    for i in idx])
    snr_min = {1: 25, 2: 20, 3: 15, 4: 10, 5: 6}[sensibilidade]
    idx, snr = idx[snr >= snr_min], snr[snr >= snr_min]
    tempos = idx * PASSO / SR + JANELA / 2 / SR
    forca = sinal[idx] / (sinal[idx].max() if len(idx) else 1)
    # quantas outras palmas em ±2 s: cenas de aplauso/ritmo têm várias seguidas
    vizinhas = [int(((np.abs(tempos - t) <= 2) & (tempos != t)).sum()) for t in tempos]
    return [(round(float(t), 3), round(float(p), 3), round(float(s), 1), v)
            for t, p, s, v in zip(tempos, forca, snr, vizinhas)]


def detectar_batidas(arquivo, inicio, duracao, bpm=None):
    """Batidas da música no trecho [inicio, inicio + duracao], em segundos a partir de inicio.

    Testa cada BPM entre 85 e 175 e fica com a grade cujos pontos caem, em média, nos
    ataques mais fortes. Depois ajusta cada batida ao ataque real mais próximo (±40 ms).
    """
    espec = espectrograma(arquivo)
    env = fluxo(espec, 30, 7000)
    qps = SR / PASSO  # quadros de análise por segundo
    trecho = env[int(inicio * qps): int((inicio + duracao) * qps)]
    trecho = trecho / (trecho.max() + 1e-9)
    n = len(trecho)

    def melhor_fase(b):
        periodo = 60 / b * qps
        fases = np.arange(0, periodo, 1.0)
        idx = np.round(fases[:, None] + np.arange(0, n, periodo)[None, :]).astype(int)
        validos = idx < n
        medias = np.where(validos, trecho[np.minimum(idx, n - 1)], 0).sum(1) / validos.sum(1)
        k = int(np.argmax(medias))
        return medias[k], fases[k]

    if bpm is None:
        candidatos = np.arange(85, 175, 0.1)
        notas = np.array([melhor_fase(b)[0] for b in candidatos])
        # picos da curva; entre os quase empatados (ex.: 90 e 180), prefere o mais perto de 120
        picos_bpm = [i for i in range(len(notas))
                     if notas[i] == notas[max(0, i - 20): i + 21].max() and notas[i] >= 0.9 * notas.max()]
        bpm = candidatos[min(picos_bpm, key=lambda i: abs(np.log2(candidatos[i] / 120)))]
    _, fase = melhor_fase(bpm)
    raio = int(0.04 * qps)
    batidas = []
    for q in np.arange(fase, n, 60 / bpm * qps):
        q = int(round(q))
        a, b = max(0, q - raio), min(n, q + raio + 1)
        local = a + int(np.argmax(trecho[a:b]))
        batidas.append((local if trecho[local] > 0.3 else q) / qps + JANELA / 2 / SR)
    return float(bpm), [t for t in batidas if t < duracao]


# ---------------------------------------------------------------- comandos

def listar(pasta, extensoes):
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() in extensoes) if pasta.exists() else []


def cmd_detectar(args):
    clipes = listar(args.clipes, EXTENSOES_VIDEO)
    if not clipes:
        sys.exit(f"Nenhum vídeo em {args.clipes}/. Coloque os trechos de filme lá.")
    linhas = []
    for clipe in clipes:
        palmas = detectar_palmas_arquivo(clipe, args.sensibilidade)
        print(f"{clipe.name}: {len(palmas)} palmas")
        linhas += [(clipe.name, *palma) for palma in palmas]
    with open(args.palmas, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arquivo", "tempo_s", "forca", "destaque_db", "palmas_vizinhas"])
        w.writerows(linhas)
    print(f"\n{len(linhas)} palmas gravadas em {args.palmas.name}. "
          "Revise e apague as linhas que não forem palmas, se quiser.")


def ler_palmas(caminho, clipes_dir, forca_min):
    if not caminho.exists():
        sys.exit(f"{caminho.name} não existe. Rode primeiro: python3 palmas.py detectar")
    duracoes, palmas = {}, []
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            if float(linha.get("forca") or 1) < forca_min:
                continue
            nome = linha["arquivo"]
            if nome not in duracoes:
                duracoes[nome] = info_midia(clipes_dir / nome)
            palmas.append((nome, float(linha["tempo_s"])))
    return palmas, duracoes


def filtro_layout(layout):
    if layout == "cortar":
        return (f"scale={LARGURA}:{ALTURA}:force_original_aspect_ratio=increase,"
                f"crop={LARGURA}:{ALTURA},setsar=1")
    # "desfoque": filme inteiro no meio, fundo desfocado (padrão dos edits de TikTok)
    return (f"split[f][b];[b]scale={LARGURA}:{ALTURA}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA}:{ALTURA},boxblur=20:2[b2];[f]scale={LARGURA}:-2[f2];"
            f"[b2][f2]overlay=(W-w)/2:(H-h)/2,setsar=1")


def planejar(batidas, duracao, palmas, duracoes, rng, batidas_por_corte):
    """Cada corte mostra uma palma caindo exatamente numa batida."""
    alvos = batidas[::batidas_por_corte]
    # limites do corte = pontos médios entre batidas-alvo, alinhados a quadros de vídeo
    limites = [0] + [round((a + b) / 2 * FPS) for a, b in zip(alvos, alvos[1:])] + [round(duracao * FPS)]
    uso, plano, anterior = {}, [], None
    for k, alvo in enumerate(alvos):
        q_ini, q_fim = limites[k], limites[k + 1]
        antes = (round(alvo * FPS) - q_ini) / FPS   # tempo mostrado antes da palma
        dur = (q_fim - q_ini) / FPS
        cands = [(nome, t) for nome, t in palmas
                 if t - antes >= 0 and t - antes + dur <= duracoes[nome][0] - 0.05
                 and duracoes[nome][1] and nome != anterior]
        if not cands:
            cands = [(nome, t) for nome, t in palmas
                     if t - antes >= 0 and t - antes + dur <= duracoes[nome][0] - 0.05 and duracoes[nome][1]]
        if not cands:
            sys.exit(f"Nenhuma palma com folga suficiente para um corte de {dur:.2f}s. "
                     "Use trechos de filme mais longos ou --batidas-por-corte menor.")
        menor_uso = min(uso.get(c, 0) for c in cands)
        nome, t = rng.choice([c for c in cands if uso.get(c, 0) == menor_uso])
        uso[(nome, t)] = uso.get((nome, t), 0) + 1
        plano.append((nome, t - antes, q_fim - q_ini))
        anterior = nome
    return plano


def renderizar(plano, clipes_dir, musica, inicio_musica, duracao, saida, args):
    cmd = [ffmpeg_bin(), "-y", "-v", "error"]
    filtros, rotulos = [], []
    layout = filtro_layout(args.layout)
    for i, (nome, ini, quadros) in enumerate(plano):
        seg = quadros / FPS
        cmd += ["-ss", f"{ini:.3f}", "-t", f"{seg + 0.5:.3f}", "-i", str(clipes_dir / nome)]
        filtros.append(f"[{i}:v]fps={FPS},trim=end_frame={quadros},setpts=PTS-STARTPTS,"
                       f"{layout.replace('[f]', f'[f{i}]').replace('[b]', f'[b{i}]').replace('[b2]', f'[bb{i}]').replace('[f2]', f'[ff{i}]')}[v{i}]")
        filtros.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                       f"atrim=0:{seg:.6f},apad=whole_dur={seg:.6f},asetpts=PTS-STARTPTS,"
                       f"volume={args.volume_filme}[a{i}]")
        rotulos.append(f"[v{i}][a{i}]")
    n = len(plano)
    filtros.append(f"{''.join(rotulos)}concat=n={n}:v=1:a=1[v][af]")
    if args.sem_musica:
        saida_audio = "[af]"
    else:
        cmd += ["-ss", f"{inicio_musica:.3f}", "-t", f"{duracao:.3f}", "-i", str(musica)]
        filtros.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=stereo,"
                       f"volume={args.volume_musica}[m]")
        filtros.append("[af][m]amix=inputs=2:duration=first:normalize=0[aout]")
        saida_audio = "[aout]"
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[v]", "-map", saida_audio,
            "-c:v", "libx264", "-preset", args.preset, "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-t", f"{duracao:.3f}",
            "-movflags", "+faststart", str(saida)]
    subprocess.run(cmd, check=True)


def cmd_montar(args):
    musicas = [args.musica] if args.musica else listar(args.pasta_musica, EXTENSOES_AUDIO)
    if not musicas:
        sys.exit(f"Nenhuma música em {args.pasta_musica}/. Coloque o arquivo da música lá.")
    musica = musicas[0]
    palmas, duracoes = ler_palmas(args.palmas, args.clipes, args.forca_minima)
    if not palmas:
        sys.exit("Nenhuma palma no palmas.csv.")

    if args.batidas:
        batidas = [float(x) - args.inicio_musica for x in args.batidas.read_text().split()]
        batidas = [b for b in batidas if 0 <= b < args.duracao]
        print(f"Música: {musica.name} | {len(batidas)} batidas do arquivo {args.batidas.name}")
    else:
        bpm, batidas = detectar_batidas(musica, args.inicio_musica, args.duracao, args.bpm)
        print(f"Música: {musica.name} | {bpm:.1f} BPM | {len(batidas)} batidas em {args.duracao:.0f}s")
    print(f"Palmas disponíveis: {len(palmas)} em {len(duracoes)} clipes\n")

    args.saida.mkdir(exist_ok=True)
    if args.misturar:
        # vários filmes no mesmo edit
        trabalhos = [(f"edit_{n:03}.mp4", palmas, args.semente + n) for n in range(1, args.quantidade + 1)]
    else:
        # padrão: cada edit usa um filme só; um (ou --edits-por-filme) edit por filme
        trabalhos = []
        for nome in dict.fromkeys(nome for nome, _ in palmas):
            do_filme = [pl for pl in palmas if pl[0] == nome]
            for k in range(1, args.edits_por_filme + 1):
                sufixo = f"_{k}" if args.edits_por_filme > 1 else ""
                trabalhos.append((f"edit_{pathlib.Path(nome).stem}{sufixo}.mp4", do_filme, args.semente + k))
    creditos = args.saida / "creditos.csv"
    novo = not creditos.exists()
    with open(creditos, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["video", "clipes_usados"])
        for n, (arquivo, grupo, semente) in enumerate(trabalhos, 1):
            destino = args.saida / arquivo
            if destino.exists() and not args.refazer:
                print(f"[{n}/{len(trabalhos)}] {arquivo} já existe, pulando")
                continue
            plano = planejar(batidas, args.duracao, grupo, duracoes, random.Random(semente), args.batidas_por_corte)
            renderizar(plano, args.clipes, musica, args.inicio_musica, args.duracao, destino, args)
            usados = sorted({pathlib.Path(nome).stem for nome, _, _ in plano})
            w.writerow([arquivo, " | ".join(usados)])
            f.flush()
            print(f"[{n}/{len(trabalhos)}] {arquivo}  ({len(plano)} cortes)")
    print(f"\nPronto! Vídeos em {args.saida}/ e lista de filmes usados em creditos.csv")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--clipes", type=pathlib.Path, default=PASTA / "clipes")
    p.add_argument("--palmas", type=pathlib.Path, default=PASTA / "palmas.csv")
    sub = p.add_subparsers(dest="comando", required=True)

    d = sub.add_parser("detectar", help="encontra as palmas nos clipes")
    m = sub.add_parser("montar", help="gera os vídeos sincronizados")
    t = sub.add_parser("tudo", help="detectar + montar")
    for s in (d, t):
        s.add_argument("--sensibilidade", type=int, choices=range(1, 6), default=3,
                       help="1 = só palmas bem nítidas ... 5 = pega tudo (mais falsos positivos)")
    for s in (m, t):
        s.add_argument("--misturar", action="store_true",
                       help="mistura filmes diferentes no mesmo edit (padrão: um filme por edit)")
        s.add_argument("--quantidade", type=int, default=100, help="nº de edits com --misturar")
        s.add_argument("--edits-por-filme", type=int, default=1, help="edits diferentes gerados de cada filme")
        s.add_argument("--refazer", action="store_true", help="gera de novo edits que já existem")
        s.add_argument("--duracao", type=float, default=30)
        s.add_argument("--pasta-musica", type=pathlib.Path, default=PASTA / "musica")
        s.add_argument("--musica", type=pathlib.Path, help="arquivo da música (padrão: o primeiro em musica/)")
        s.add_argument("--inicio-musica", type=float, default=0, help="segundo da música onde o edit começa")
        s.add_argument("--bpm", type=float, help="força o BPM se a detecção errar")
        s.add_argument("--batidas", type=pathlib.Path,
                       help="arquivo .txt com os segundos exatos das batidas (substitui a detecção)")
        s.add_argument("--batidas-por-corte", type=int, default=2,
                       help="1 = troca de cena a cada batida (frenético), 2 = a cada 2 batidas...")
        s.add_argument("--layout", choices=["desfoque", "cortar"], default="desfoque")
        s.add_argument("--volume-filme", type=float, default=0.6, help="volume do som original das cenas")
        s.add_argument("--volume-musica", type=float, default=1.0)
        s.add_argument("--sem-musica", action="store_true",
                       help="exporta sem a música, para adicionar o som direto no TikTok")
        s.add_argument("--forca-minima", type=float, default=0.3,
                       help="ignora palmas mais fracas que isso, relativo à mais forte do clipe (0 a 1)")
        s.add_argument("--semente", type=int, default=0, help="mude para gerar outra leva de combinações")
        s.add_argument("--preset", default="veryfast", help="preset do x264 (mais lento = arquivo menor)")
        s.add_argument("--saida", type=pathlib.Path, default=PASTA / "saida")
    args = p.parse_args()

    if args.comando in ("detectar", "tudo"):
        cmd_detectar(args)
    if args.comando in ("montar", "tudo"):
        cmd_montar(args)


if __name__ == "__main__":
    main()
