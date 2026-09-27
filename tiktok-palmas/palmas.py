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


# ---------------------------------------------------------------- análise de imagem

ANALISE_FPS = 30
ANALISE_LARGURA = 160


def analisar_imagem(arquivo):
    """Movimento por coluna da imagem, quadro a quadro, e os cortes de câmera do vídeo.

    Guarda o resultado em clipes/.analise/ para não recalcular.
    """
    cache = arquivo.parent / ".analise" / (arquivo.name + ".npz")
    if cache.exists() and cache.stat().st_mtime >= arquivo.stat().st_mtime:
        d = np.load(cache)
        if "barras" in d.files:
            return {k: d[k] for k in d.files}
    r = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(arquivo)],
                       capture_output=True, text=True, errors="replace")
    w0, h0 = map(int, re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", r.stderr).groups())
    altura = int(round(ANALISE_LARGURA * h0 / w0 / 2)) * 2
    proc = subprocess.Popen(
        [ffmpeg_bin(), "-v", "error", "-i", str(arquivo), "-an", "-vf",
         f"fps={ANALISE_FPS},scale={ANALISE_LARGURA}:{altura},format=gray", "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE)
    tam = ANALISE_LARGURA * altura
    colunas, global_, conteudo, linhas, anterior = [], [], [], [], None
    while True:
        dados = proc.stdout.read(tam * 300)
        if not dados:
            break
        quadros = np.frombuffer(dados[: len(dados) // tam * tam], np.uint8).reshape(-1, altura, ANALISE_LARGURA)
        quadros = quadros.astype(np.int16)
        # quanto da imagem não é fundo liso (créditos e telas de texto ficam perto de 0)
        mediana = np.median(quadros.reshape(len(quadros), -1), axis=1)[:, None, None]
        conteudo.append((np.abs(quadros - mediana) > 40).mean(axis=(1, 2)).astype(np.float32))
        linhas.append(quadros[::10].mean(axis=2))  # brilho médio de cada linha da imagem
        if anterior is not None:
            quadros = np.concatenate([anterior[None], quadros])
        dif = np.abs(np.diff(quadros, axis=0))
        # ignora o chuvisco de compressão (diferenças pequenas)
        colunas.append(np.where(dif > 12, dif, 0).sum(axis=1).astype(np.float32))
        global_.append(dif.mean(axis=(1, 2)).astype(np.float32))
        anterior = quadros[-1]
    proc.wait()
    colunas = np.concatenate(colunas) if colunas else np.zeros((0, ANALISE_LARGURA), np.float32)
    global_ = np.concatenate(global_) if global_ else np.zeros(0, np.float32)
    # corte de câmera: salto brusco na imagem inteira, bem acima do normal em volta
    cortes = []
    for i in range(len(global_)):
        viz = global_[max(0, i - 15): i + 16]
        if global_[i] > 18 and global_[i] > 4 * np.median(viz) + 4:
            cortes.append((i + 1) / ANALISE_FPS)
    # tarjas pretas (letterbox): linhas de cima/baixo quase sempre pretas
    brilho = np.median(np.concatenate(linhas), axis=0) if linhas else np.zeros(altura)
    escuras = brilho < 20
    topo = int(np.argmin(escuras)) if not escuras.all() else 0
    base = int(np.argmin(escuras[::-1])) if not escuras.all() else 0
    barras = np.array([topo / altura, base / altura]) if topo + base < altura * 0.6 else np.zeros(2)
    d = {"colunas": colunas, "cortes": np.array(cortes), "barras": barras,
         "proporcao": np.array(w0 / h0 * (1 / max(0.4, 1 - barras.sum()))),
         "conteudo": np.concatenate(conteudo) if conteudo else np.zeros(0, np.float32)}
    cache.parent.mkdir(exist_ok=True)
    np.savez_compressed(cache, **d)
    return d


def janela_recorte(proporcao):
    """Largura do recorte vertical 9:16, em colunas da análise."""
    return max(4, min(ANALISE_LARGURA, int(round(ANALISE_LARGURA * (9 / 16) / proporcao))))


def movimento_no_recorte(an, t_ini, t_fim):
    """Melhor posição (centro, 0 a 1) do recorte vertical e o movimento dentro dele no intervalo."""
    a, b = int(t_ini * ANALISE_FPS), max(int(t_ini * ANALISE_FPS) + 1, int(t_fim * ANALISE_FPS))
    perfil = an["colunas"][a:b].sum(axis=0)
    w = janela_recorte(float(an["proporcao"]))
    soma = np.convolve(perfil, np.ones(w), "valid")
    if len(soma) == 0:
        return 0.5, 0.0
    k = int(np.argmax(soma))
    return (k + w / 2) / ANALISE_LARGURA, float(soma[k]) / max(1, b - a)


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
    batidas, forcas = [], []
    for q in np.arange(fase, n, 60 / bpm * qps):
        q = int(round(q))
        a, b = max(0, q - raio), min(n, q + raio + 1)
        local = a + int(np.argmax(trecho[a:b]))
        t = (local if trecho[local] > 0.3 else q) / qps + JANELA / 2 / SR
        if t < duracao:
            batidas.append(t)
            forcas.append(float(trecho[a:b].max()))
    return float(bpm), batidas, forcas


# ---------------------------------------------------------------- comandos

def listar(pasta, extensoes):
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() in extensoes) if pasta.exists() else []


def cmd_detectar(args):
    clipes = listar(args.clipes, EXTENSOES_VIDEO)
    if not clipes:
        sys.exit(f"Nenhum vídeo em {args.clipes}/. Coloque os trechos de filme lá.")
    linhas = []
    for clipe in clipes:
        sens = args.sensibilidade
        palmas = detectar_palmas_arquivo(clipe, sens)
        # vídeos com música por cima escondem as palmas: sobe a sensibilidade sozinho
        # (as palmas falsas que entrarem são descartadas depois pela análise da imagem)
        while len(palmas) < 80 and sens < 5:
            sens += 1
            palmas = detectar_palmas_arquivo(clipe, sens)
        print(f"{clipe.name}: {len(palmas)} palmas (sensibilidade {sens})")
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
            forca = float(linha.get("forca") or 1)
            if forca < forca_min:
                continue
            nome = linha["arquivo"]
            if nome not in duracoes:
                duracoes[nome] = info_midia(clipes_dir / nome)
            palmas.append((nome, float(linha["tempo_s"]), forca))
    return palmas, duracoes


def filtro_layout(layout, centro_x=0.5, barras=(0, 0)):
    topo, base = barras
    tira = (f"crop=iw:ih*{1 - topo - base:.4f}:0:ih*{topo:.4f}," if topo + base > 0.02 else "")
    return tira + _filtro_layout(layout, centro_x)


def _filtro_layout(layout, centro_x):
    if layout == "cortar":
        # tela cheia vertical, recortando na região onde está a ação (centro_x, de 0 a 1)
        return (f"scale={LARGURA}:{ALTURA}:force_original_aspect_ratio=increase,"
                f"crop={LARGURA}:{ALTURA}:'min(max(iw*{centro_x:.4f}-{LARGURA // 2},0),iw-{LARGURA})':"
                f"'(ih-{ALTURA})/2',setsar=1")
    # "desfoque": filme inteiro no meio, fundo desfocado
    return (f"split[f][b];[b]scale={LARGURA}:{ALTURA}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA}:{ALTURA},boxblur=20:2[b2];[f]scale={LARGURA}:-2[f2];"
            f"[b2][f2]overlay=(W-w)/2:(H-h)/2,setsar=1")


def regularidade(tempos):
    """Para cada palma: quantas palmas vizinhas (±3 s) caem num mesmo ritmo que ela.

    Palmas de verdade se repetem em intervalos regulares; estalos de fala, portas etc. não.
    """
    ts = np.asarray(tempos)
    periodos = np.arange(0.25, 1.6, 0.01)
    notas = []
    for t in ts:
        d = np.abs(ts[(np.abs(ts - t) <= 3) & (ts != t)] - t)
        if len(d) == 0:
            notas.append(0)
            continue
        k = np.round(d[None, :] / periodos[:, None])
        ok = (k >= 1) & (np.abs(d[None, :] - k * periodos[:, None]) < 0.035)
        notas.append(max(len(set(k[i][ok[i]])) for i in range(len(periodos))))
    return np.array(notas)


def preparar_candidatos(palmas, duracoes, clipes_dir):
    """Junta som e imagem: cada palma ganha uma nota de 'dá para ver alguém batendo palma'."""
    analises, cands = {}, []
    for nome in dict.fromkeys(n for n, _, _ in palmas):
        if not duracoes[nome][1]:
            continue
        analises[nome] = analisar_imagem(clipes_dir / nome)
        do_filme = [(t, f) for n, t, f in palmas if n == nome]
        vis = np.array([movimento_no_recorte(analises[nome], t - 0.3, t + 0.1)[1] for t, _ in do_filme])
        ref = np.percentile(vis, 80) + 1e-9 if len(vis) else 1
        conteudo = analises[nome]["conteudo"]
        ritmo = regularidade([t for t, _ in do_filme])
        minimo_ritmo = 3 if (ritmo >= 3).sum() >= 40 else 2
        for (t, forca), v, r in zip(do_filme, vis, ritmo):
            if r < minimo_ritmo:  # palma solta, fora de qualquer ritmo: provavelmente não é palma
                continue
            nota_vis = min(1.5, v / ref)
            if nota_vis < 0.25:  # nada se mexendo na imagem: palma "falsa" ou tela parada
                continue
            a = max(0, int((t - 0.3) * ANALISE_FPS))
            if conteudo[a: a + 12].mean() < 0.12:  # créditos / tela de texto
                continue
            cands.append({"nome": nome, "t": t, "nota": (forca ** 0.5) * nota_vis})
    return cands, analises


def planejar(batidas, forcas, duracao, cands, analises, duracoes, rng, batidas_por_corte, cronologico):
    """Cortes caem nas batidas e cada palma cai na batida forte seguinte.

    Com 2 batidas por corte: troca de cena numa batida, palma na próxima (a mais forte do par),
    mostrando meia batida de "mãos se aproximando" antes da palma.
    """
    periodo = float(np.median(np.diff(batidas))) if len(batidas) > 1 else 0.5
    passo = max(1, batidas_por_corte)
    fase = max(range(passo), key=lambda p: np.mean(forcas[p::passo]))
    alvos = batidas[fase::passo]
    antes = periodo * (passo - 1) if passo > 1 else periodo / 2
    limites = [0] + [round(max(0, a - antes) * FPS) for a in alvos[1:]] + [round(duracao * FPS)]

    tempos = [c["t"] for c in cands]
    lo, hi = (min(tempos), max(tempos)) if tempos else (0, 1)
    n = len(alvos)
    plano, usados, anterior, t_anterior = [], [], None, -1e9
    for k, alvo in enumerate(alvos):
        q_ini, q_fim = limites[k], limites[k + 1]
        lead = (round(alvo * FPS) - q_ini) / FPS   # tempo mostrado antes da palma
        dur = (q_fim - q_ini) / FPS
        meta = lo + (k + 0.5) / n * (hi - lo)     # ponto do vídeo que este corte deve mostrar
        melhores = []
        # 1ª tentativa: palmas ainda não usadas; se faltar material, aceita repetir uma
        for repetir in (False, True):
            for c in cands:
                nome, t = c["nome"], c["t"]
                ini, fim = t - lead, t - lead + dur
                if ini < 0 or fim > duracoes[nome][0] - 0.1:
                    continue
                cortes = analises[nome]["cortes"]
                if np.any((cortes > ini + 0.04) & (cortes < fim - 0.04)):
                    continue  # o trecho atravessaria um corte de câmera do vídeo original
                repetida = any(u[0] == nome and abs(u[1] - t) < max(0.3, dur / 2) for u in usados)
                if repetida and not repetir:
                    continue
                custo = -2.0 * c["nota"] + rng.uniform(0, 0.4) + (4 if repetida else 0)
                if cronologico:
                    custo += 1.5 * abs(t - meta) / max(1e-9, (hi - lo) / n)
                    if t < t_anterior:
                        custo += 3
                elif nome == anterior:
                    custo += 2
                melhores.append((custo, nome, t, ini, fim))
            if melhores:
                break
        if not melhores:
            sys.exit(f"Sem palmas suficientes para montar o corte {k + 1} de {n}. "
                     "Mande vídeos com mais palmas ou use --batidas-por-corte 4.")
        _, nome, t, ini, fim = min(melhores)
        centro, _ = movimento_no_recorte(analises[nome], ini, fim)
        plano.append((nome, ini, q_fim - q_ini, centro, tuple(analises[nome]["barras"])))
        usados.append((nome, t))
        anterior, t_anterior = nome, t
    return plano


def renderizar(plano, clipes_dir, musica, inicio_musica, duracao, saida, args):
    cmd = [ffmpeg_bin(), "-y", "-v", "error"]
    filtros, rotulos = [], []
    for i, (nome, ini, quadros, centro, barras) in enumerate(plano):
        seg = quadros / FPS
        layout = filtro_layout(args.layout, centro, barras)
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
        forcas = [1.0] * len(batidas)
        print(f"Música: {musica.name} | {len(batidas)} batidas do arquivo {args.batidas.name}")
    else:
        bpm, batidas, forcas = detectar_batidas(musica, args.inicio_musica, args.duracao, args.bpm)
        print(f"Música: {musica.name} | {bpm:.1f} BPM | {len(batidas)} batidas em {args.duracao:.0f}s")
    print("Analisando a imagem dos vídeos...")
    cands, analises = preparar_candidatos(palmas, duracoes, args.clipes)
    print(f"Palmas aproveitáveis: {len(cands)} de {len(palmas)} em {len(analises)} vídeos\n")

    args.saida.mkdir(exist_ok=True)
    if args.misturar:
        trabalhos = [(f"edit_{n:03}.mp4", cands, args.semente + n) for n in range(1, args.quantidade + 1)]
    else:
        # padrão: cada edit usa um vídeo só
        trabalhos = []
        for nome in analises:
            do_filme = [c for c in cands if c["nome"] == nome]
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
            plano = planejar(batidas, forcas, args.duracao, grupo, analises, duracoes,
                             random.Random(semente), args.batidas_por_corte, not args.misturar)
            renderizar(plano, args.clipes, musica, args.inicio_musica, args.duracao, destino, args)
            usados = sorted({pathlib.Path(nome).stem for nome, *_ in plano})
            w.writerow([arquivo, " | ".join(usados)])
            f.flush()
            inicio, fim = plano[0][1], plano[-1][1]
            print(f"[{n}/{len(trabalhos)}] {arquivo}  ({len(plano)} cortes, "
                  f"do segundo {inicio:.0f} ao {fim:.0f} do vídeo)")
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
        s.add_argument("--sensibilidade", type=int, choices=range(1, 6), default=4,
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
        s.add_argument("--layout", choices=["desfoque", "cortar"], default="cortar")
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
