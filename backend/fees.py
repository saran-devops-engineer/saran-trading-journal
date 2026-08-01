def calculate_fees(trade_type, side, entry_price, exit_price, quantity, exchange='NSE'):
    trade_type = trade_type.lower()
    side = side.lower()
    entry = float(entry_price) if entry_price else 0
    exit_p = float(exit_price) if exit_price else 0
    qty = float(quantity) if quantity else 0

    entry_value = entry * qty
    exit_value = exit_p * qty if exit_p else 0
    total_turnover = entry_value + exit_value

    fees = {
        'brokerage': 0,
        'stt': 0,
        'exchange_charges': 0,
        'gst': 0,
        'sebi_charges': 0,
        'stamp_duty': 0,
        'ipft': 0,
        'total_fees': 0,
        'pnl_before_fees': 0,
        'pnl_after_fees': 0,
    }

    if entry_value == 0:
        return fees

    if side == 'long':
        pnl = (exit_p - entry) * qty if exit_p else 0
    else:
        pnl = (entry - exit_p) * qty if exit_p else 0

    fees['pnl_before_fees'] = round(pnl, 2)

    if trade_type == 'stock':
        fees.update(_calc_equity_fees(side, entry, exit_p, qty, exchange))
    elif trade_type == 'option':
        fees.update(_calc_option_fees(side, entry, exit_p, qty, exchange))
    elif trade_type == 'future':
        fees.update(_calc_future_fees(side, entry, exit_p, qty, exchange))

    total = (fees['brokerage'] + fees['stt'] + fees['exchange_charges'] +
             fees['gst'] + fees['sebi_charges'] + fees['stamp_duty'] + fees['ipft'])
    fees['total_fees'] = round(total, 2)
    fees['pnl_after_fees'] = round(pnl - total, 2)

    return fees


def _calc_equity_fees(side, entry, exit_p, qty, exchange):
    entry_value = entry * qty
    exit_value = exit_p * qty if exit_p else 0

    brokerage = 0

    stt = entry_value * 0.001
    if exit_value > 0:
        stt += exit_value * 0.001

    total_value = entry_value + exit_value if exit_value > 0 else entry_value
    if exchange == 'BSE':
        exchange_charges = total_value * 0.0000375
    else:
        exchange_charges = total_value * 0.0000297

    sebi_charges = total_value * 0.000001

    stamp_duty = entry_value * 0.00015

    ipft = total_value * 0.000001

    taxable = brokerage + exchange_charges + sebi_charges + ipft
    gst = taxable * 0.18

    return {
        'brokerage': round(brokerage, 2),
        'stt': round(stt, 2),
        'exchange_charges': round(exchange_charges, 2),
        'gst': round(gst, 2),
        'sebi_charges': round(sebi_charges, 2),
        'stamp_duty': round(stamp_duty, 2),
        'ipft': round(ipft, 2),
    }


def _calc_option_fees(side, entry, exit_p, qty, exchange):
    entry_value = entry * qty
    exit_value = exit_p * qty if exit_p else 0

    brokerage = 20
    if exit_value > 0:
        brokerage += 20

    stt = 0
    if exit_value > 0:
        stt = exit_value * 0.000625

    total_value = entry_value + exit_value if exit_value > 0 else entry_value
    if exchange == 'BSE':
        exchange_charges = total_value * 0.00005
    else:
        exchange_charges = total_value * 0.0003503

    sebi_charges = total_value * 0.000001

    stamp_duty = entry_value * 0.00003

    ipft = total_value * 0.000005

    taxable = brokerage + exchange_charges + sebi_charges + ipft
    gst = taxable * 0.18

    return {
        'brokerage': round(brokerage, 2),
        'stt': round(stt, 2),
        'exchange_charges': round(exchange_charges, 2),
        'gst': round(gst, 2),
        'sebi_charges': round(sebi_charges, 2),
        'stamp_duty': round(stamp_duty, 2),
        'ipft': round(ipft, 2),
    }


def _calc_future_fees(side, entry, exit_p, qty, exchange):
    entry_value = entry * qty
    exit_value = exit_p * qty if exit_p else 0

    brokerage = 20
    if exit_value > 0:
        brokerage += 20

    stt = 0
    if exit_value > 0:
        stt = exit_value * 0.000125

    total_value = entry_value + exit_value if exit_value > 0 else entry_value
    if exchange == 'BSE':
        exchange_charges = 0
    else:
        exchange_charges = total_value * 0.0000173

    sebi_charges = total_value * 0.000001

    stamp_duty = entry_value * 0.00002

    ipft = total_value * 0.000001

    taxable = brokerage + exchange_charges + sebi_charges + ipft
    gst = taxable * 0.18

    return {
        'brokerage': round(brokerage, 2),
        'stt': round(stt, 2),
        'exchange_charges': round(exchange_charges, 2),
        'gst': round(gst, 2),
        'sebi_charges': round(sebi_charges, 2),
        'stamp_duty': round(stamp_duty, 2),
        'ipft': round(ipft, 2),
    }
