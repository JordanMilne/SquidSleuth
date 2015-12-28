from sqlalchemy import (
    Binary,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class LogObjectMixin(object):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    # Meaning this is when we fetched it, not necessarily when it happened
    date_approx = Column(Boolean, default=False)


class SeenClient(Base, LogObjectMixin):
    __tablename__ = "seen_clients"
    ip = Column(String(45), index=True)


class SeenDomain(Base, LogObjectMixin):
    __tablename__ = "seen_domains"
    domain = Column(String(256), index=True)


class SeenRequest(Base, LogObjectMixin):
    __tablename__ = "seen_requests"
    domain = Column(String(256), index=True)
    # seen_domain = relationship("SeenClient")
    # seen_domain_id = Column(Integer, ForeignKey("seen_domains.id"))
    # If we pulled this from /objects we won't have the info of who originally
    # requested it. ;(
    client = Column(String(45), index=True, nullable=True)
    # seen_client = relationship("SeenClient")
    # seen_client_id = Column(Integer, ForeignKey("seen_clients.id"), nullable=True)
    uri = Column(String(), index=True)
