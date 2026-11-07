class Producto:
    """Entidad de catálogo: precio y si exige receta los define el negocio, no el cajero."""

    def __init__(self, id_producto: str, nombre: str, precio: float, requiere_receta: bool = False):
        self.id_producto = id_producto
        self.nombre = nombre
        self.precio = precio
        self.requiere_receta = requiere_receta
