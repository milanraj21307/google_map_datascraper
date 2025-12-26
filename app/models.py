from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    state = Column(String)
    name = Column(String)
    address = Column(String)

    rating = Column(String)
    company_type = Column(String)

    phone = Column(String)
    email = Column(String)
    website = Column(String)
    source = Column(String)

    ceo = Column(String, default="UNKNOWN")
    ceo_source = Column(String)

    validation_status = Column(String)

    # ✅ NEW FIELDS
    processing_status = Column(String, default="pending")  # pending | processing | done | error
    processed = Column(Boolean, default=False)
