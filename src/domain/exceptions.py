class ReglaDeNegocioExcepcion(Exception):
    pass

class ProductoCaducadoError(ReglaDeNegocioExcepcion):
    pass

class LoteRetiradoError(ReglaDeNegocioExcepcion):
    pass

class StockInsuficienteError(ReglaDeNegocioExcepcion):
    pass

class DatosDeRecetaIncompletosError(ReglaDeNegocioExcepcion):
    pass

class VentaYaCerradaError(ReglaDeNegocioExcepcion):
    pass
