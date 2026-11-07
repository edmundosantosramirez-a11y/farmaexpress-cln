"""Modelo relacional. El dominio no depende de esto: los repositorios mapean en ambos sentidos."""
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductoModel(Base):
    __tablename__ = "productos"

    id_producto: Mapped[str] = mapped_column(String(50), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    precio: Mapped[float] = mapped_column(Float)
    requiere_receta: Mapped[bool] = mapped_column(Boolean, default=False)


class LoteModel(Base):
    __tablename__ = "lotes"

    id_lote: Mapped[str] = mapped_column(String(50), primary_key=True)
    id_producto: Mapped[str] = mapped_column(String(50), index=True)
    fecha_caducidad: Mapped[date] = mapped_column(Date)
    stock: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    # Control de concurrencia optimista (U3, Etapa 5): dos cajas no descuentan la misma existencia.
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    __mapper_args__ = {"version_id_col": version}


class VentaModel(Base):
    __tablename__ = "ventas"

    id_venta: Mapped[str] = mapped_column(String(50), primary_key=True)
    id_sucursal: Mapped[str] = mapped_column(String(50))
    id_cajero: Mapped[str] = mapped_column(String(50))
    estado: Mapped[str] = mapped_column(String(20))
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    receta_folio: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receta_cedula_medico: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receta_nombre_medico: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    receta_fecha_emision: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    lineas: Mapped[List["LineaVentaModel"]] = relationship(
        back_populates="venta",
        cascade="all, delete-orphan",
        order_by="LineaVentaModel.id",
        lazy="selectin",
    )


class LineaVentaModel(Base):
    __tablename__ = "lineas_venta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_venta: Mapped[str] = mapped_column(String(50), ForeignKey("ventas.id_venta"), index=True)
    id_producto: Mapped[str] = mapped_column(String(50))
    id_lote: Mapped[str] = mapped_column(String(50))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Float)
    requiere_receta: Mapped[bool] = mapped_column(Boolean, default=False)

    venta: Mapped["VentaModel"] = relationship(back_populates="lineas")
