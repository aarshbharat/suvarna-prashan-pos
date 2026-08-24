from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Account, engine 
from pricing import calculate_price
from database import (
    SessionLocal,
    Account,
    ProductVariant,
    ProductPricing,
    Invoice,
    InvoiceItem,
    Product,
    engine
)
from sqlalchemy import or_

class AccountCreate(BaseModel):
    account_id: str
    account_name: str
    address: str
    city: str
    state: str
    pincode: str
    mobile_number: str
    email: str | None
    gst_number: str | None
    contact_person: str

class PricingCreate(BaseModel):
    sku: str
    state_type: str
    price_per_dosage: float
    gst_rate: float
    effective_from: date

class InvoiceItemCreate(BaseModel):
    sku: str
    quantity: int


class InvoiceCreate(BaseModel):
    account_id: str
    invoice_date: date
    items: list[InvoiceItemCreate]

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Billing System API"}

account_list = []

@app.post("/accounts/")
async def create_account(account: AccountCreate):
    # Here you can add logic to save the account to a database or perform other actions
    db = SessionLocal()

    db_account = Account(
        account_id=account.account_id,
        account_name=account.account_name,
        address=account.address,
        city=account.city,
        state=account.state,
        pincode=account.pincode,
        mobile_number=account.mobile_number,
        email=account.email,
        gst_number=account.gst_number,
        contact_person=account.contact_person
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    db.close()
    # account_list.append(account)

    return {
        "message": "Account created successfully",
        "account": account
    }
    # return {"message": "Account created successfully", "account": account}

@app.get("/accounts/")
async def get_accounts(search: str | None = None):

    db = SessionLocal()

    query = db.query(Account)

    if search:
        query = query.filter(
            or_(
                Account.account_name.ilike(f"%{search}%"),
                Account.mobile_number.ilike(f"%{search}%")
            )
        )

    accounts = query.order_by(
        Account.account_name
    ).all()

    result = []

    for account in accounts:
        result.append({
            "account_id": account.account_id,
            "account_name": account.account_name,
            "address": account.address,
            "city": account.city,
            "state": account.state,
            "pincode": account.pincode,
            "mobile_number": account.mobile_number,
            "email": account.email,
            "gst_number": account.gst_number,
            "contact_person": account.contact_person
        })

    db.close()

    return {
        "accounts": result
    }

@app.get("/accounts/{account_id}")
async def get_account(account_id: str):
    db = SessionLocal()
    account = db.query(Account).filter(Account.account_id == account_id).first()
    db.close()
    return {"account": account}

@app.get("/db-test")
async def db_test():
    with engine.connect() as connection:
        return {"message": "Database connected!"}

@app.get("/pricing/{account_id}/{sku}/{quantity}")
async def get_price(account_id: str, sku: str, quantity: int):

    db = SessionLocal()

    account = db.query(Account).filter(
        Account.account_id == account_id
    ).first()

    if account is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    variant = db.query(ProductVariant).filter(
        ProductVariant.sku == sku
    ).first()

    if variant is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Product variant not found"
        )

    if account.state.lower() == "gujarat":
        state_type = "Gujarat"
    else:
        state_type = "Other"

    pricing = db.query(ProductPricing).filter(
        ProductPricing.product_variant_id == variant.id,
        ProductPricing.state_type == state_type
    ).first()

    if pricing is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Pricing not found"
        )

    price = calculate_price(
        float(pricing.price_per_dosage),
        variant.dosage,
        quantity
    )

    db.close()

    return {
        "account_id": account.account_id,
        "account_name": account.account_name,
        "state": account.state,
        "sku": variant.sku,
        "variant": variant.variant_name,
        "dosage": variant.dosage,
        "pricing": price
    }

@app.post("/pricing/")
async def create_pricing(pricing: PricingCreate):

    db = SessionLocal()

    variant = db.query(ProductVariant).filter(
        ProductVariant.sku == pricing.sku
    ).first()

    if variant is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Product variant not found"
        )

    existing_pricing = db.query(ProductPricing).filter(
        ProductPricing.product_variant_id == variant.id,
        ProductPricing.state_type == pricing.state_type,
        ProductPricing.effective_from == pricing.effective_from
    ).first()

    if existing_pricing:
        db.close()
        raise HTTPException(
            status_code=409,
            detail="Pricing already exists for this SKU, state and effective date"
        )

    new_pricing = ProductPricing(
        product_variant_id=variant.id,
        state_type=pricing.state_type,
        price_per_dosage=pricing.price_per_dosage,
        gst_rate=pricing.gst_rate,
        effective_from=pricing.effective_from
    )

    db.add(new_pricing)
    db.commit()
    db.refresh(new_pricing)

    db.close()

    return {
        "message": "Pricing created successfully",
        "pricing": new_pricing
    }

@app.post("/invoices/")
async def create_invoice(invoice: InvoiceCreate):

    db = SessionLocal()

    account = db.query(Account).filter(
        Account.account_id == invoice.account_id
    ).first()

    if account is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    total_taxable_value = 0
    total_cgst = 0
    total_sgst = 0
    grand_total = 0

    calculated_items = []

    for item in invoice.items:

        variant = db.query(ProductVariant).filter(
            ProductVariant.sku == item.sku
        ).first()

        if variant is None:
            db.close()
            raise HTTPException(
                status_code=404,
                detail=f"Product variant {item.sku} not found"
            )

        if account.state.lower() == "gujarat":
            state_type = "Gujarat"
        else:
            state_type = "Other"

        pricing = (
            db.query(ProductPricing)
            .filter(
                ProductPricing.product_variant_id == variant.id,
                ProductPricing.state_type == state_type,
                ProductPricing.effective_from <= invoice.invoice_date
            )
            .order_by(ProductPricing.effective_from.desc())
            .first()
        )

        if pricing is None:
            db.close()
            raise HTTPException(
                status_code=404,
                detail=f"Pricing not found for {item.sku}"
            )

        price = calculate_price(
            float(pricing.price_per_dosage),
            variant.dosage,
            item.quantity
        )

        total_taxable_value += price["taxable_value"]
        total_cgst += price["cgst"]
        total_sgst += price["sgst"]
        grand_total += price["total_price"]

        calculated_items.append({
            "variant": variant,
            "quantity": item.quantity,
            "pricing": price
        })

    # Generate invoice number
    last_invoice = (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .first()
    )

    if last_invoice is None:
        invoice_number = "INV-0001"
    else:
        invoice_number = f"INV-{last_invoice.id + 1:04d}"

    # Create invoice
    new_invoice = Invoice(
        invoice_number=invoice_number,
        account_id=account.id,
        invoice_date=invoice.invoice_date,
        total_amount=grand_total
    )

    db.add(new_invoice)
    db.flush()

    # Create invoice items
    for item in calculated_items:

        new_item = InvoiceItem(
            invoice_id=new_invoice.id,
            product_variant_id=item["variant"].id,
            quantity=item["quantity"],
            dosage=item["variant"].dosage,
            price_per_dosage=item["pricing"]["price_per_dosage"],
            taxable_amount=item["pricing"]["taxable_value"],
            cgst=item["pricing"]["cgst"],
            sgst=item["pricing"]["sgst"],
            total_amount=item["pricing"]["total_price"]
        )

        db.add(new_item)

    db.commit()
    db.refresh(new_invoice)

    # Save values before closing the database session
    account_id = account.account_id
    account_name = account.account_name
    saved_invoice_number = new_invoice.invoice_number

    db.close()

    return {
        "message": "Invoice created successfully",
        "invoice_number": saved_invoice_number,
        "invoice_date": new_invoice.invoice_date,
        "account_id": account_id,
        "account_name": account_name,
        "summary": {
            "total_taxable_value": round(total_taxable_value, 2),
            "total_cgst": round(total_cgst, 2),
            "total_sgst": round(total_sgst, 2),
            "grand_total": round(grand_total, 2)
        }
    }

@app.get("/invoices/{invoice_number}")
async def get_invoice(invoice_number: str):

    db = SessionLocal()

    invoice = db.query(Invoice).filter(
        Invoice.invoice_number == invoice_number
    ).first()

    if invoice is None:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    items = db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice.id
    ).all()

    account = db.query(Account).filter(
        Account.id == invoice.account_id
    ).first()

    result_items = []
    total_taxable_value = 0
    total_cgst = 0
    total_sgst = 0

    for item in items:

        variant = db.query(ProductVariant).filter(
            ProductVariant.id == item.product_variant_id
        ).first()

        result_items.append({
            "sku": variant.sku,
            "variant": variant.variant_name,
            "quantity": item.quantity,
            "dosage": item.dosage,
            "price_per_dosage": float(item.price_per_dosage),
            "taxable_amount": float(item.taxable_amount),
            "cgst": float(item.cgst),
            "sgst": float(item.sgst),
            "total_amount": float(item.total_amount)
        })

        total_taxable_value += float(item.taxable_amount)
        total_cgst += float(item.cgst)
        total_sgst += float(item.sgst)

    response = {
    "invoice_number": invoice.invoice_number,
    "account_id": account.account_id,
    "account_name": account.account_name,
    "items": result_items,
    "summary": {
        "total_taxable_value": round(total_taxable_value, 2),
        "cgst": round(total_cgst, 2),
        "sgst": round(total_sgst, 2),
        "total_gst": round(total_cgst + total_sgst, 2),
        "grand_total": float(invoice.total_amount)
    }
}

    db.close()

    return response

@app.get("/invoices/")
async def get_invoices():

    db = SessionLocal()

    invoices = (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .all()
    )

    result = []

    for invoice in invoices:

        account = db.query(Account).filter(
            Account.id == invoice.account_id
        ).first()

        items = db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id == invoice.id
        ).all()

        total_dose = sum(
            item.quantity * item.dosage
            for item in items
        )

        result.append({
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "account_id": account.account_id,
            "account_name": account.account_name,
            "total_dose": total_dose,
            "total_amount": float(invoice.total_amount)
        })

    db.close()

    return {
        "invoices": result
    }

@app.get("/products/")
async def get_products():

    db = SessionLocal()

    products = db.query(Product).all()

    result = []

    for product in products:

        variants = db.query(ProductVariant).filter(
            ProductVariant.product_id == product.id
        ).all()

        result.append({
            "product_id": product.product_id,
            "product_name": product.product_name,
            "variants": [
                {
                    "sku": variant.sku,
                    "variant_name": variant.variant_name,
                    "dosage": variant.dosage
                }
                for variant in variants
            ]
        })

    db.close()

    return {
        "products": result
    }