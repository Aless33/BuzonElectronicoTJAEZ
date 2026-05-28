import unittest
import uuid
from django.utils import timezone
from web.services import generar_qr_provisional

class TestGenerarQR(unittest.TestCase):

    def setUp(self):
        self.datos_base = {
            "tipo_promocion": "DEMANDA",
            "correo_ciudadano": "usuario@ejemplo.com",
            "numero_sobres": 1
        }

    def test_generacion_uuid_v4_formato(self):
        qr_bytes, metadatos = generar_qr_provisional(self.datos_base)
        uuid_generado = metadatos['uuid']
        
        try:
            val_obj = uuid.UUID(uuid_generado, version=4)
            es_valido = str(val_obj) == uuid_generado
        except ValueError:
            es_valido = False
            
        self.assertTrue(es_valido, "El identificador generado no es un UUID v4 válido")

    def test_asignacion_caducidad_23_59(self):
        qr_bytes, metadatos = generar_qr_provisional(self.datos_base)
        caducidad = metadatos['fecha_caducidad']
        
        hora_minuto = caducidad.strftime('%H:%M')
        self.assertEqual(hora_minuto, '23:59', "La caducidad no está configurada a las 23:59")

    def test_qrs_unicos_por_lote(self):
        self.datos_base["numero_sobres"] = 5
        uuids_generados = []
        
        for _ in range(self.datos_base["numero_sobres"]):
            _, metadatos = generar_qr_provisional(self.datos_base)
            uuids_generados.append(metadatos['uuid'])
        
        duplicados = False
        lista_verificacion = []
        for id_qr in uuids_generados:
            if id_qr in lista_verificacion:
                duplicados = True
                break
            lista_verificacion.append(id_qr)
            
        self.assertFalse(duplicados, "Se encontraron UUIDs duplicados en el lote generado")
        
    def test_fallo_por_falta_de_sobres(self):
        self.datos_base["numero_sobres"] = 0
        with self.assertRaises(ValueError) as context:
            generar_qr_provisional(self.datos_base)
            
        self.assertTrue("El número de sobres debe ser al menos 1." in str(context.exception))

    def test_falta_tipo_promocion(self):
        self.datos_base.pop("tipo_promocion")
        with self.assertRaises(ValueError) as context:
            generar_qr_provisional(self.datos_base)
        
        self.assertEqual(str(context.exception), "El tipo de promoción es obligatorio.")

    def test_numero_sobres_tipo_incorrecto(self):
        self.datos_base["numero_sobres"] = "uno"
        with self.assertRaises(ValueError) as context:
            generar_qr_provisional(self.datos_base)
        
        self.assertEqual(str(context.exception), "El número de sobres debe ser al menos 1.")

    def test_numero_sobres_negativo(self):
        self.datos_base["numero_sobres"] = -5
        with self.assertRaises(ValueError) as context:
            generar_qr_provisional(self.datos_base)
        
        self.assertEqual(str(context.exception), "El número de sobres debe ser al menos 1.")

    def test_duplicados_generacion_multiple(self):
        uuids_generados = []
        
        for _ in range(50):
            _, metadatos = generar_qr_provisional(self.datos_base)
            uuids_generados.append(metadatos['uuid'])
        
        duplicados = False
        lista_verificacion = []
        for id_qr in uuids_generados:
            if id_qr in lista_verificacion:
                duplicados = True
                break
            lista_verificacion.append(id_qr)
            
        self.assertFalse(duplicados, "Se encontraron UUIDs duplicados en ejecuciones consecutivas.")

if __name__ == '__main__':
    unittest.main()