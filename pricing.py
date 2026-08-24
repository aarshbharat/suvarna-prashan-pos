GST_RATE = 0.05


def calculate_price(price_per_dosage: float, dosage: int, quantity: int):

    total_price = price_per_dosage * dosage * quantity

    taxable_value = total_price / (1 + GST_RATE)
    cgst = taxable_value * 0.025
    sgst = taxable_value * 0.025

    return {
        "price_per_dosage": price_per_dosage,
        "dosage": dosage,
        "quantity": quantity,
        "total_price": total_price,
        "taxable_value": round(taxable_value, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2)
    }