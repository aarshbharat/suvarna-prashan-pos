import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Date
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    account_id = Column(String, unique=True, nullable=False)
    account_name = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    mobile_number = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    gst_number = Column(String, unique=True, nullable=True)
    contact_person = Column(String, nullable=False)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    product_id = Column(String, unique=True, nullable=False)
    product_name = Column(String, unique=True, nullable=False)

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True, nullable=False)
    variant_name = Column(String, nullable=False)
    dosage = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)

    invoice_number = Column(
        String,
        unique=True,
        nullable=False
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False
    )

    invoice_date = Column(
        Date,
        nullable=False
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)

    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=False
    )

    product_variant_id = Column(
        Integer,
        ForeignKey("product_variants.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)
    dosage = Column(Integer, nullable=False)

    price_per_dosage = Column(
        Numeric(10, 2),
        nullable=False
    )

    taxable_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    cgst = Column(
        Numeric(10, 2),
        nullable=False
    )

    sgst = Column(
        Numeric(10, 2),
        nullable=False
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

class ProductPricing(Base):
    __tablename__ = "product_pricing"

    id = Column(Integer, primary_key=True)

    product_variant_id = Column(
        Integer,
        ForeignKey("product_variants.id"),
        nullable=False
    )

    state_type = Column(String, nullable=False)
    price_per_dosage = Column(Numeric(10, 2), nullable=False)

    gst_rate = Column(Numeric(5, 2), nullable=False, default=5.00)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)


Base.metadata.create_all(engine)

# db = SessionLocal()

# product = Product(
#     product_id="PROD001",
#     product_name="Suvarna Prashan"
# )

# db.add(product)
# db.commit()
# db.refresh(product)

# print("Product created:", product.product_id)

# db.close()

# db = SessionLocal()

# product = db.query(Product).filter(
#     Product.product_id == "PROD001"
# ).first()

# variant_5 = ProductVariant(
#     sku="SKU-5",
#     variant_name="5 Dose Bottle",
#     dosage=5,
#     product_id=product.id
# )

# variant_10 = ProductVariant(
#     sku="SKU-10",
#     variant_name="10 Dose Bottle",
#     dosage=10,
#     product_id=product.id
# )

# db.add_all([variant_5, variant_10])
# db.commit()

# db.close()

# from datetime import date

# db = SessionLocal()

# sku_5 = db.query(ProductVariant).filter(
#     ProductVariant.sku == "SKU-5"
# ).first()

# sku_10 = db.query(ProductVariant).filter(
#     ProductVariant.sku == "SKU-10"
# ).first()

# pricing_data = [
#     ProductPricing(
#         product_variant_id=sku_5.id,
#         state_type="Gujarat",
#         price_per_dosage=34,
#         gst_rate=5,
#         effective_from=date.today()
#     ),
#     ProductPricing(
#         product_variant_id=sku_5.id,
#         state_type="Other",
#         price_per_dosage=35,
#         gst_rate=5,
#         effective_from=date.today()
#     ),
#     ProductPricing(
#         product_variant_id=sku_10.id,
#         state_type="Gujarat",
#         price_per_dosage=34,
#         gst_rate=5,
#         effective_from=date.today()
#     ),
#     ProductPricing(
#         product_variant_id=sku_10.id,
#         state_type="Other",
#         price_per_dosage=35,
#         gst_rate=5,
#         effective_from=date.today()
#     )
# ]

# db.add_all(pricing_data)
# db.commit()
# db.close()