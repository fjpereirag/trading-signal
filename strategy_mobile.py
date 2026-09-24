import numpy as np


# ============================================================
# TRADING SIGNAL V4
# Motor de decision + contexto + zonas + riesgo
# MODO: SIMULACION / ALERTAS
# No ejecuta ordenes reales
# ============================================================


def indicators(df, cfg):
    x = df.copy()

    # STOCHASTIC
    lo = x["Low"].rolling(cfg["stoch_k"]).min()
    hi = x["High"].rolling(cfg["stoch_k"]).max()
    den = (hi - lo).replace(0, np.nan)

    x["K"] = 100 * (x["Close"] - lo) / den
    x["D"] = x["K"].rolling(cfg["stoch_d"]).mean()

    # EMAs
    x["EMA200"] = x["Close"].ewm(
        span=cfg["ema_fast"],
        adjust=False
    ).mean()

    x["EMA365"] = x["Close"].ewm(
        span=cfg["ema_slow"],
        adjust=False
    ).mean()

    # RSI 14
    delta = x["Close"].diff()

    gain = delta.clip(lower=0).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)

    # ATR 14
    prev_close = x["Close"].shift(1)

    tr = np.maximum(
        (x["High"] - x["Low"]).abs(),
        np.maximum(
            (x["High"] - prev_close).abs(),
            (x["Low"] - prev_close).abs()
        )
    )

    x["ATR"] = tr.ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    # Rango dinamico para zonas de valor
    x["HIGH20"] = x["High"].rolling(20).max()
    x["LOW20"] = x["Low"].rolling(20).min()

    return x


def market_zone(row):
    """
    Clasifica el precio dentro del rango reciente:
    ALTA / MEDIA / BAJA / PROFUNDA
    """

    high = row["HIGH20"]
    low = row["LOW20"]
    price = row["Close"]

    if np.isnan(high) or np.isnan(low) or high <= low:
        return "DESCONOCIDA", 0.5

    position = (price - low) / (high - low)

    if position >= 0.75:
        zone = "ALTA"
    elif position >= 0.45:
        zone = "MEDIA"
    elif position >= 0.20:
        zone = "BAJA"
    else:
        zone = "PROFUNDA"

    return zone, float(position)


def classify_context(m15, m5):
    """
    Contexto principal V4.
    """

    ema_gap = abs(
        m15["EMA200"] - m15["EMA365"]
    ) / m15["Close"] * 100

    atr_pct = (
        m15["ATR"] / m15["Close"] * 100
        if m15["Close"] else 0
    )

    bullish = (
        m15["Close"] > m15["EMA200"] > m15["EMA365"]
    )

    bearish = (
        m15["Close"] < m15["EMA200"] < m15["EMA365"]
    )

    momentum_up = m5["K"] > m5["D"]
    momentum_down = m5["K"] < m5["D"]

    if bullish and momentum_up:
        context = "ALCISTA"
    elif bearish and momentum_down:
        context = "BAJISTA"
    else:
        context = "NEUTRO"

    return {
        "context": context,
        "ema_gap_pct": float(ema_gap),
        "atr_pct": float(atr_pct)
    }


def risk_guard(
    balance=None,
    free_margin=None,
    exposure_pct=None,
    max_exposure_pct=30.0
):
    """
    Motor de proteccion V4.

    IMPORTANTE:
    No garantiza ausencia de perdidas.
    Solo aplica reglas programadas de control de riesgo.
    """

    result = {
        "safe": True,
        "block_buys": False,
        "protect_margin": False,
        "message": "RIESGO OK"
    }

    if (
        exposure_pct is not None
        and exposure_pct >= max_exposure_pct
    ):
        result["safe"] = False
        result["block_buys"] = True
        result["message"] = "EXPOSICION MAXIMA"

    if (
        balance is not None
        and free_margin is not None
        and balance > 0
    ):
        margin_ratio = free_margin / balance

        result["margin_ratio"] = margin_ratio

        if margin_ratio < 0.40:
            result["safe"] = False
            result["block_buys"] = True
            result["protect_margin"] = True
            result["message"] = "PROTEGER MARGEN"

    return result


def position_review(
    protected_balance,
    trading_balance,
    trading_power,
    allocated_power,
    max_exposure_pct,
    quantity,
    average_price,
    observed_price,
):
    """Read-only assessment of manually entered Quantfury account snapshots.

    The document's 'free margin' has no confirmed Quantfury equivalent.
    Consequently the 40% check is a warning based on trading balance, not
    a claim about the broker's liquidation or margin rules.
    """
    if protected_balance <= 0 or trading_power <= 0 or quantity < 0:
        raise ValueError("Saldo real y poder de trading deben ser positivos.")
    if min(trading_balance, allocated_power, average_price, observed_price) < 0:
        raise ValueError("Los importes y precios no pueden ser negativos.")

    threshold = protected_balance * 0.40
    exposure_pct = allocated_power / trading_power * 100
    pnl_estimate = quantity * (observed_price - average_price)
    return {
        "threshold": threshold,
        "trading_balance_gap": trading_balance - threshold,
        "balance_warning": trading_balance < threshold,
        "exposure_pct": exposure_pct,
        "exposure_warning": exposure_pct >= max_exposure_pct,
        "available_power": trading_power - allocated_power,
        "pnl_estimate": pnl_estimate,
        "profit_target_met": pnl_estimate >= 50,
        "estimated_change_per_cent": quantity * 0.01,
    }


def analyze(tfs, cfg):
    """
    Analisis V4 compatible con la aplicacion V3.1.
    """

    z = {
        k: indicators(v, cfg)
        for k, v in tfs.items()
    }

    m15 = z["M15"].iloc[-1]
    m5 = z["M5"].iloc[-1]
    m1 = z["M1"].iloc[-1]
    p1 = z["M1"].iloc[-2]

    # --------------------------------------------------------
    # 1. TENDENCIA M15
    # --------------------------------------------------------

    up = (
        m15.Close > m15.EMA200 > m15.EMA365
    )

    down = (
        m15.Close < m15.EMA200 < m15.EMA365
    )

    trend = (
        "BUY"
        if up
        else "SELL"
        if down
        else "WAIT"
    )

    # --------------------------------------------------------
    # 2. CONFIRMACION M5
    # --------------------------------------------------------

    confirm = False

    if trend == "BUY":
        confirm = (
            m5.K > m5.D
            and m5.Close > m5.EMA200
        )

    elif trend == "SELL":
        confirm = (
            m5.K < m5.D
            and m5.Close < m5.EMA200
        )

    # --------------------------------------------------------
    # 3. GATILLO M1
    # --------------------------------------------------------

    trigger = False

    if trend == "BUY":
        trigger = (
            p1.K <= p1.D
            and m1.K > m1.D
        )

    elif trend == "SELL":
        trigger = (
            p1.K >= p1.D
            and m1.K < m1.D
        )

    score = (
        int(trend != "WAIT")
        + int(confirm)
        + int(trigger)
    )

    raw_signal = (
        trend
        if score == 3
        else "WAIT"
    )

    # --------------------------------------------------------
    # 4. FILTROS DE CALIDAD
    # --------------------------------------------------------

    ema_sep = (
        abs(m15.EMA200 - m15.EMA365)
        / m15.Close
        * 100
    )

    ema_ok = ema_sep >= 0.08

    if raw_signal == "BUY":
        rsi_ok = 52 <= m15.RSI <= 72

    elif raw_signal == "SELL":
        rsi_ok = 28 <= m15.RSI <= 48

    else:
        rsi_ok = False

    if raw_signal == "BUY":
        momentum_ok = (
            m5.K > m5.D
            and m1.K > m1.D
        )

    elif raw_signal == "SELL":
        momentum_ok = (
            m5.K < m5.D
            and m1.K < m1.D
        )

    else:
        momentum_ok = False

    atr_pct = (
        m15.ATR / m15.Close * 100
    )

    atr_ok = 0.05 <= atr_pct <= 3.0

    filters = {
        "ema": bool(ema_ok),
        "rsi": bool(rsi_ok),
        "momentum": bool(momentum_ok),
        "atr": bool(atr_ok)
    }

    quality_points = sum(filters.values())

    if quality_points == 4:
        quality = "ALTA"

    elif quality_points >= 2:
        quality = "MEDIA"

    else:
        quality = "BAJA"

    signal = raw_signal

    if signal != "WAIT" and quality == "BAJA":
        signal = "WAIT"

    # --------------------------------------------------------
    # 5. CONTEXTO V4
    # --------------------------------------------------------

    context_data = classify_context(m15, m5)

    zone, zone_position = market_zone(m15)

    # Detectamos retroceso respecto al cierre anterior M15
    prev_m15 = z["M15"].iloc[-2]

    change_pct = (
        (m15.Close - prev_m15.Close)
        / prev_m15.Close
        * 100
    )

    if change_pct <= -1.5:
        pullback = "PROFUNDO"

    elif change_pct <= -0.25:
        pullback = "REAL"

    elif change_pct < 0:
        pullback = "SUAVE"

    else:
        pullback = "NO"

    # --------------------------------------------------------
    # 6. DECISION V4
    # --------------------------------------------------------

    action = "ESPERAR"

    if (
        context_data["context"] == "ALCISTA"
        and zone == "BAJA"
        and pullback in ("REAL", "PROFUNDO")
    ):
        action = "PREPARAR_COMPRA"

    if (
        context_data["context"] == "ALCISTA"
        and zone == "PROFUNDA"
        and pullback in ("REAL", "PROFUNDO")
    ):
        action = "PREPARAR_COMPRA_ADICIONAL"

    # La señal tecnica 3/3 sigue siendo necesaria
    # para convertir PREPARAR en una señal operativa.
    if action.startswith("PREPARAR") and signal != "BUY":
        action = "ESPERAR_CONFIRMACION"

    # --------------------------------------------------------
    # 7. MOTIVO
    # --------------------------------------------------------

    reason = (
        f"M15={trend} | "
        f"M5={'OK' if confirm else 'NO'} | "
        f"M1={'OK' if trigger else 'NO'} | "
        f"Score={score}/3 | "
        f"Contexto={context_data['context']} | "
        f"Zona={zone} | "
        f"Retroceso={pullback} | "
        f"Accion={action}"
    )

    # Confirmed breakout: last completed M15 close above the preceding 20
    # completed highs, with a completed M5 close above its preceding 20 highs.
    # These are external market candles; broker prices govern position decisions.
    breakout = bool(
        context_data["context"] == "ALCISTA"
        and len(z["M15"]) >= 22 and len(z["M5"]) >= 22
        and m15.Close > z["M15"]["High"].iloc[-21:-1].max()
        and m5.Close > z["M5"]["High"].iloc[-21:-1].max()
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {
        "signal": signal,
        "raw_signal": raw_signal,
        "quality": quality,
        "score": score,
        "trend": trend,
        "confirm": bool(confirm),
        "trigger": bool(trigger),
        "breakout": breakout,
        "filters": filters,

        "price": float(m1.Close),

        "metrics": {
            "ema_sep_pct": float(ema_sep),
            "rsi": float(m15.RSI),
            "atr_pct": float(atr_pct),
            "m15_k": float(m15.K),
            "m15_d": float(m15.D),
            "m5_k": float(m5.K),
            "m5_d": float(m5.D),
            "m1_k": float(m1.K),
            "m1_d": float(m1.D)
        },

        # Nuevos campos V4
        "context": context_data["context"],
        "zone": zone,
        "zone_position": zone_position,
        "pullback": pullback,
        "action": action,

        "reason": reason
    }


def trade_plan(
    price,
    side,
    balance,
    risk_pct,
    sl_pct,
    tp_pct
):
    """
    Plan de operacion de referencia.
    NO ejecuta ordenes.
    """

    risk_cash = (
        balance * risk_pct / 100
    )

    if side == "BUY":
        stop = price * (
            1 - sl_pct / 100
        )

        target = price * (
            1 + tp_pct / 100
        )

    elif side == "SELL":
        stop = price * (
            1 + sl_pct / 100
        )

        target = price * (
            1 - tp_pct / 100
        )

    else:
        return {
            "risk_cash": risk_cash,
            "stop": None,
            "target": None,
            "qty_reference": 0
        }

    risk_per_unit = abs(price - stop)

    qty = (
        risk_cash / risk_per_unit
        if risk_per_unit > 0
        else 0
    )

    return {
        "risk_cash": float(risk_cash),
        "stop": float(stop),
        "target": float(target),
        "qty_reference": float(qty)
    }
