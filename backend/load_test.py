# ═══════════════════════════════════════════════════════════
#  EMANTIX PRO — Script de Prueba de Carga (Locust)
#  Simula usuarios concurrentes contra la API
# ═══════════════════════════════════════════════════════════

from locust import HttpUser, task, between, events
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmantixUser(HttpUser):
    """
    Simula un usuario típico de EMANTIC PRO
    
    Comportamiento:
    1. Login
    2. Acceder a dashboard
    3. Consultar datos
    4. Navegar a diferentes secciones
    """
    
    wait_time = between(1, 3)  # Esperar 1-3 segundos entre acciones
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
    
    def on_start(self):
        """
        Se ejecuta cuando el usuario comienza.
        Realiza login.
        """
        self.login()
    
    def login(self):
        """
        POST /api/auth/login
        Simula un usuario autenticándose
        """
        with self.client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "Admin123!"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.user_data = data.get("user")
                response.success()
                logger.info(f"✓ Login exitoso: {self.user_data.get('username')}")
            else:
                response.failure(f"Login falló: {response.status_code}")
                logger.error(f"✗ Login falló: {response.text}")
    
    def get_headers(self):
        """Retorna headers con token de autenticación"""
        return {
            "Authorization": f"Bearer {self.access_token}"
        } if self.access_token else {}
    
    # ── TAREAS (Tasks) ──────────────────────────────────────
    
    @task(3)
    def get_dashboard(self):
        """
        GET /api/health (dashboard health check)
        Tarea frecuente: usuario verifica estado del sistema
        """
        with self.client.get(
            "/api/health",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check falló: {response.status_code}")
    
    @task(2)
    def get_maintenance(self):
        """
        GET /api/maintenance
        Tarea frecuente: listar mantenimiento
        """
        with self.client.get(
            "/api/maintenance",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"GET /maintenance falló: {response.status_code}")
    
    @task(2)
    def get_reportes(self):
        """
        GET /api/reportes
        Tarea frecuente: listar reportes
        """
        with self.client.get(
            "/api/reportes",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"GET /reportes falló: {response.status_code}")
    
    @task(2)
    def get_manuals(self):
        """
        GET /api/manuals
        Tarea frecuente: listar manuales
        """
        with self.client.get(
            "/api/manuals",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"GET /manuals falló: {response.status_code}")
    
    @task(1)
    def get_me(self):
        """
        GET /api/auth/me
        Tarea moderada: obtener información del usuario
        """
        with self.client.get(
            "/api/auth/me",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                self.user_data = response.json()
                response.success()
            else:
                response.failure(f"GET /auth/me falló: {response.status_code}")
    
    @task(1)
    def refresh_token(self):
        """
        POST /api/auth/refresh
        Tarea moderada: refrescar token
        """
        with self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Token refresh falló: {response.status_code}")


class AdminUser(EmantixUser):
    """
    Simula un usuario admin con tareas adicionales
    """
    
    @task(1)
    def list_users(self):
        """
        GET /api/users
        Tarea admin: listar usuarios
        """
        with self.client.get(
            "/api/users",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 403]:  # 403 si no es admin
                response.success()
            else:
                response.failure(f"GET /users falló: {response.status_code}")
    
    @task(0.5)
    def get_health_full(self):
        """
        GET /api/health/full
        Tarea admin: estado completo (solo admin)
        """
        with self.client.get(
            "/api/health/full",
            headers=self.get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"GET /health/full falló: {response.status_code}")


# ═══════════════════════════════════════════════════════════
# Event Handlers (Métrica de Eventos)
# ═══════════════════════════════════════════════════════════

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta al iniciar las pruebas"""
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("PRUEBA DE CARGA — EMANTIC PRO")
    logger.info("═══════════════════════════════════════════════════════")
    logger.info(f"URL: {environment.host}")
    logger.info("Iniciando pruebas de carga...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al terminar las pruebas"""
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("PRUEBA DE CARGA COMPLETADA")
    logger.info("═══════════════════════════════════════════════════════")
    print_summary(environment)


def print_summary(environment):
    """
    Imprime resumen de resultados
    """
    logger.info("\n")
    logger.info("RESUMEN DE RESULTADOS:")
    logger.info("─" * 60)
    
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    
    if total_requests > 0:
        success_rate = ((total_requests - total_failures) / total_requests) * 100
    else:
        success_rate = 0
    
    logger.info(f"Total de requests: {total_requests}")
    logger.info(f"Total de fallos: {total_failures}")
    logger.info(f"Tasa de éxito: {success_rate:.2f}%")
    logger.info(f"Response time (median): {stats.total.get_median_response_time():.2f}ms")
    logger.info(f"Response time (95%): {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"Response time (99%): {stats.total.get_response_time_percentile(0.99):.2f}ms")
    logger.info(f"RPS (requests/sec): {stats.total.total_rps:.2f}")
    
    # Detalle por endpoint
    logger.info("\n")
    logger.info("DETALLE POR ENDPOINT:")
    logger.info("─" * 60)
    
    for name, stats_entry in stats.entries.items():
        logger.info(f"\n{name}")
        logger.info(f"  Requests: {stats_entry.num_requests}")
        logger.info(f"  Failures: {stats_entry.num_failures}")
        if stats_entry.num_requests > 0:
            success = ((stats_entry.num_requests - stats_entry.num_failures) / stats_entry.num_requests) * 100
            logger.info(f"  Success rate: {success:.2f}%")
        logger.info(f"  Median: {stats_entry.get_median_response_time():.2f}ms")
        logger.info(f"  95th: {stats_entry.get_response_time_percentile(0.95):.2f}ms")


# ═══════════════════════════════════════════════════════════
# Configuración para ejecutar
# ═══════════════════════════════════════════════════════════

"""
CÓMO EJECUTAR:

1. Instalar Locust:
   pip install locust

2. Ejecutar contra localhost:
   locust -f load_test.py -H http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s

3. Ejecutar contra servidor remoto:
   locust -f load_test.py -H http://api.example.com --users 50 --spawn-rate 5 --run-time 300s

4. Headless (sin interfaz web):
   locust -f load_test.py -H http://localhost:8000 --headless --users 100 --spawn-rate 10 --run-time 300s

PARÁMETROS:
  --users N:         Número máximo de usuarios simultáneos
  --spawn-rate N:    Usuarios agregados por segundo
  --run-time Xs:     Duración de la prueba (en segundos)
  --headless:        Modo CLI sin interfaz web
  -H URL:            URL del servidor a probar

NIVELES SUGERIDOS:
  Nivel 1: 10 usuarios, spawn-rate 1, 60 segundos
  Nivel 2: 50 usuarios, spawn-rate 5, 300 segundos
  Nivel 3: 100 usuarios, spawn-rate 10, 300 segundos
"""
