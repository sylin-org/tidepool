from . import correction, datacenter, grind, sycophancy

MEASURES = {
    "grind": grind.run,
    "sycophancy": sycophancy.run,
    "correction": correction.run,
    "datacenter": datacenter.run,
}

NEEDS_JUDGE = {"grind", "datacenter"}
