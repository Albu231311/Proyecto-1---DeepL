"""
generador.py
Genera transacciones sintéticas de tarjetas para el Proyecto 1 (Monitoreo Transaccional).

Diseño:
- N clientes con perfiles heterogéneos (frecuencia, monto típico, comercios preferidos, canal).
- Transacciones "normales" simuladas como proceso de llegadas por día (Poisson) durante `periodo_dias`.
- 3 tipos de fraude inyectados en un subconjunto de clientes:
    1. "escalada"   -> ORDEN-DEPENDIENTE: varias compras pequeñas seguidas de una grande.
    2. "rafaga"     -> velocidad alta en poco tiempo (bien capturado por agregados de conteo).
    3. "comercio_atipico" -> compra grande en comercio nunca antes usado por ESE cliente
                             (verificado contra su historial real), hora inusual.
                             No depende del orden. Se predice, ANTES de correr ningún
                             modelo, que el Modelo A tendrá dificultad aquí: el feature
                             set solo incluye frecuencia GLOBAL del comercio y diversidad
                             en 7 días, no una señal causal de "primera vez de este
                             cliente en este comercio" -> es el caso de falla esperado
                             que pide el enunciado, justificado por el diseño de
                             features, no por haber visto resultados.
- Con la MISMA semilla, produce siempre el mismo dataset (reproducibilidad).

Features agregadas (calculadas de forma CAUSAL: solo con historial pasado de cada cliente,
nunca con información futura -> evita fuga de información):
    - monto_prom_24h
    - n_trans_ultima_hora
    - monto_max_dia
    - diversidad_comercios_7d
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass

MERCHANT_CATEGORIES = [
    "supermercado", "restaurante", "gasolinera", "farmacia", "ropa",
    "electronica", "streaming", "viajes", "hogar", "entretenimiento",
    "salud", "educacion", "ferreteria", "belleza", "mascotas",
    "deportes", "joyeria", "electrodomesticos", "licoreria", "otros",
]
N_MERCHANTS = len(MERCHANT_CATEGORIES)
CHANNELS = ["POS", "online", "cajero"]


@dataclass
class Config:
    n_clientes: int = 3000
    periodo_dias: int = 180
    tasa_fraude_clientes: float = 0.08    # % de clientes que sufren al menos un episodio de fraude
    seed: int = 42


def _perfil_clientes(rng, cfg: Config) -> pd.DataFrame:
    """Crea un perfil heterogéneo por cliente (esto es lo que hace que los datos parezcan reales)."""
    n = cfg.n_clientes
    # frecuencia diaria de transacciones ~ Gamma (algunos clientes transaccionan mucho, otros poco)
    lam_diario = rng.gamma(shape=2.0, scale=0.35, size=n) + 0.05
    # monto típico ~ lognormal por cliente
    mu_monto = rng.normal(loc=5.2, scale=0.6, size=n)     # ln(monto) media
    sigma_monto = rng.uniform(0.25, 0.55, size=n)
    # comercios preferidos: cada cliente tiene 3-5 comercios "de siempre"
    n_pref = rng.integers(3, 6, size=n)
    comercios_pref = [rng.choice(N_MERCHANTS, size=k, replace=False) for k in n_pref]
    canal_pref = rng.choice(len(CHANNELS), size=n)  # canal dominante del cliente

    return pd.DataFrame({
        "client_id": np.arange(n),
        "lam_diario": lam_diario,
        "mu_monto": mu_monto,
        "sigma_monto": sigma_monto,
        "comercios_pref": comercios_pref,
        "canal_pref": canal_pref,
    })


def _generar_normales(rng, perfiles: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Genera transacciones legítimas para todos los clientes durante todo el periodo."""
    filas = []
    for _, p in perfiles.iterrows():
        for dia in range(cfg.periodo_dias):
            n_trans_dia = rng.poisson(p.lam_diario)
            if n_trans_dia == 0:
                continue
            horas = np.sort(rng.uniform(0, 24, size=n_trans_dia))
            for h in horas:
                # 85% de las veces usa un comercio preferido, 15% explora otro
                if rng.random() < 0.85:
                    comercio = rng.choice(p.comercios_pref)
                else:
                    comercio = rng.integers(0, N_MERCHANTS)
                # 80% usa su canal preferido
                canal = p.canal_pref if rng.random() < 0.8 else rng.integers(0, len(CHANNELS))
                monto = rng.lognormal(mean=p.mu_monto, sigma=p.sigma_monto)
                filas.append((int(p.client_id), dia, h, monto, comercio, canal, "legitimo", 0))
    return pd.DataFrame(filas, columns=[
        "client_id", "dia", "hora_del_dia", "amount", "merchant", "channel", "fraud_type", "label"
    ])


def _inyectar_fraudes(rng, perfiles: pd.DataFrame, normales: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Inyecta episodios de fraude en un subconjunto de clientes. Devuelve solo las filas de fraude.

    `normales` se recibe para poder consultar el historial REAL de cada cliente al
    construir el fraude de tipo `comercio_atipico` (ver fix del comercio "nunca usado").
    """
    n_fraude = max(1, int(cfg.n_clientes * cfg.tasa_fraude_clientes))
    clientes_fraude = rng.choice(perfiles.client_id.values, size=n_fraude, replace=False)
    tipos = rng.choice(["escalada", "rafaga", "comercio_atipico"], size=n_fraude,
                        p=[0.4, 0.3, 0.3])  # más peso al tipo order-dependent

    filas = []
    for cid, tipo in zip(clientes_fraude, tipos):
        p = perfiles.loc[perfiles.client_id == cid].iloc[0]
        # FIX: antes se dejaba un margen de 5 dias al final ("periodo_dias - 5") que
        # garantizaba 0 fraudes en los ultimos 5 dias del periodo (artefacto temporal).
        # Los episodios caben dentro de un mismo dia, asi que no hace falta ese margen;
        # solo dejamos 7 dias de historia inicial para que existan datos previos.
        dia = rng.integers(7, cfg.periodo_dias)
        hora_base = rng.uniform(1, 22)
        monto_tipico = np.exp(p.mu_monto)

        if tipo == "escalada":
            # ORDEN-DEPENDIENTE: 3-5 compras chicas -> 1 compra grande, en ventana corta (mismo día)
            n_chicas = rng.integers(3, 6)
            for k in range(n_chicas):
                h = min(23.9, hora_base + k * rng.uniform(0.05, 0.2))
                monto = monto_tipico * rng.uniform(0.15, 0.35)
                filas.append((cid, dia, h, monto, rng.choice(p.comercios_pref),
                              p.canal_pref, "escalada", 1))
            h_final = min(23.9, hora_base + n_chicas * 0.2 + 0.1)
            monto_final = monto_tipico * rng.uniform(6, 10)
            filas.append((cid, dia, h_final, monto_final, rng.integers(0, N_MERCHANTS),
                          rng.integers(0, len(CHANNELS)), "escalada", 1))

        elif tipo == "rafaga":
            # velocidad alta: 8-12 transacciones en ~30-45 min, montos moderados, comercios variados
            n_trans = rng.integers(8, 13)
            ventana_h = rng.uniform(0.4, 0.7)
            horas = np.sort(hora_base + rng.uniform(0, ventana_h, size=n_trans))
            for h in horas:
                monto = monto_tipico * rng.uniform(0.5, 1.5)
                filas.append((cid, dia, min(23.9, h), monto, rng.integers(0, N_MERCHANTS),
                              rng.integers(0, len(CHANNELS)), "rafaga", 1))

        else:  # comercio_atipico
            # una sola transacción grande, comercio REALMENTE nunca usado por este cliente
            # hasta este punto del tiempo, hora inusual (madrugada).
            # FIX: antes se excluian solo los comercios_pref (los "favoritos"), pero un 15%
            # de las transacciones legitimas visitan otros comercios, asi que "no preferido"
            # no era lo mismo que "nunca usado". Ahora consultamos el historial real del
            # cliente ANTES del dia de fraude en `normales` para garantizar que el comercio
            # elegido de verdad no aparece en su historia.
            h = rng.uniform(1, 4.5)
            hist_cliente = normales[(normales.client_id == cid) & (normales.dia < dia)]
            comercios_usados_hist = set(hist_cliente["merchant"].unique())
            comercios_no_usados = [m for m in range(N_MERCHANTS) if m not in comercios_usados_hist]
            if not comercios_no_usados:  # cliente ya visito los 20 comercios (muy raro)
                comercios_no_usados = [m for m in range(N_MERCHANTS) if m not in p.comercios_pref]
            comercio = rng.choice(comercios_no_usados)
            monto = monto_tipico * rng.uniform(4, 8)
            filas.append((cid, dia, h, monto, comercio, rng.integers(0, len(CHANNELS)),
                          "comercio_atipico", 1))

    return pd.DataFrame(filas, columns=[
        "client_id", "dia", "hora_del_dia", "amount", "merchant", "channel", "fraud_type", "label"
    ])


def _calcular_features_causales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula, para cada transacción, features agregadas usando SOLO transacciones
    anteriores del mismo cliente (nunca futuras -> sin fuga de información).
    """
    df = df.sort_values(["client_id", "timestamp"]).reset_index(drop=True)
    out_prom24h = np.zeros(len(df))
    out_n_hora = np.zeros(len(df))
    out_max_dia = np.zeros(len(df))
    out_div_7d = np.zeros(len(df))

    for cid, grupo in df.groupby("client_id", sort=False):
        idx = grupo.index.values
        ts = grupo["timestamp"].values
        montos = grupo["amount"].values
        dias = grupo["dia"].values
        comercios = grupo["merchant"].values

        hist_ts, hist_monto, hist_comercio = [], [], []
        for i in range(len(idx)):
            t = ts[i]
            # purgar historial fuera de la ventana de 7 días (la más larga que usamos)
            while hist_ts and (t - hist_ts[0]) > 7 * 24:
                hist_ts.pop(0); hist_monto.pop(0); hist_comercio.pop(0)

            en_24h = [m for h, m in zip(hist_ts, hist_monto) if (t - h) <= 24]
            en_1h = [h for h in hist_ts if (t - h) <= 1]
            en_dia = [m for h, m in zip(hist_ts, hist_monto) if int(h // 24) == int(t // 24)]
            en_7d = set(hist_comercio)

            out_prom24h[idx[i]] = np.mean(en_24h) if en_24h else 0.0
            out_n_hora[idx[i]] = len(en_1h)
            out_max_dia[idx[i]] = max(en_dia) if en_dia else 0.0
            out_div_7d[idx[i]] = len(en_7d)

            hist_ts.append(t); hist_monto.append(montos[i]); hist_comercio.append(comercios[i])

    df["monto_prom_24h"] = out_prom24h
    df["n_trans_ultima_hora"] = out_n_hora
    df["monto_max_dia"] = out_max_dia
    df["diversidad_comercios_7d"] = out_div_7d
    return df


def generar_dataset(cfg: Config = Config()) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    perfiles = _perfil_clientes(rng, cfg)
    normales = _generar_normales(rng, perfiles, cfg)
    fraudes = _inyectar_fraudes(rng, perfiles, normales, cfg)

    df = pd.concat([normales, fraudes], ignore_index=True)
    df["timestamp"] = df["dia"] * 24.0 + df["hora_del_dia"]  # horas desde el inicio del periodo
    df = df.sort_values(["client_id", "timestamp"]).reset_index(drop=True)

    df = _calcular_features_causales(df)

    # orden dentro de la secuencia de cada cliente (útil para el Modelo B de tu compañero)
    df["seq_index"] = df.groupby("client_id").cumcount()
    df["transaction_id"] = np.arange(len(df))
    df["merchant_name"] = df["merchant"].map(lambda i: MERCHANT_CATEGORIES[i])
    df["channel_name"] = df["channel"].map(lambda i: CHANNELS[i])

    cols = ["transaction_id", "client_id", "seq_index", "dia", "timestamp", "amount",
            "merchant", "merchant_name", "channel", "channel_name",
            "monto_prom_24h", "n_trans_ultima_hora", "monto_max_dia", "diversidad_comercios_7d",
            "fraud_type", "label"]
    return df[cols]


if __name__ == "__main__":
    d = generar_dataset()
    print(d.shape)
    print(d["label"].mean())
    print(d["fraud_type"].value_counts())
