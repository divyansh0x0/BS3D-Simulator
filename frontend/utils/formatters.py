def format_scientific_unicode(val: float) -> str:
    if val == 0:
        return "0.00"
    s = f"{val:.2e}"
    mantissa, exp_str = s.split("e")
    exp_int = int(exp_str)
    if exp_int == 0:
        return f"{float(mantissa):.2f}"
    if -2 <= exp_int <= 2:
        return f"{val:.2f}"

    superscripts = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }
    exp_unicode = "".join(superscripts.get(c, c) for c in str(exp_int))
    return f"{mantissa} × 10{exp_unicode}"
